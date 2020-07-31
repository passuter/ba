import os
import pyshark
import statistics
import threading
import sys
from tkinter import filedialog

import server_frontend, server
from data_structures import *

raw_res_fold:str
res_fold:str = ""
delete_files_after_processing:bool

measuring_intervall = 0.1 #in seconds

def init():
    """
    Initializes global variables
    """
    global raw_res_fold, delete_files_after_processing
    delete_files_after_processing = True
    raw_res_fold = server.results_folder + "/"

factor = {
    "b": 1,
    "K": 1000,
    "M": 10**6,
    "G": 10**9,
}

def begin_processing():
    """
    Starts the processing of the data in a new thread
    """
    conf = server_frontend.active_config
    state = server_frontend.state
    threading.Thread(target=start_processing, args=(conf, state)).start()

def begin_processing_manual():
    """
    Starts the processing of the data manually (i.e. without running the server)
    """
    init()
    args = sys.argv
    for arg in args:
        if arg == '-no_del' or arg == '-nodel':
            global delete_files_after_processing
            delete_files_after_processing = False
            print("Not deleting files")

    conf = server_frontend.load_conf()
    if not conf:
        print("No configuration selected")
        return
    state = State(conf)
    state.started = True
    state.pull_complete = True
    for dev_conf in conf.dev_configs:
        state.dev_status[dev_conf.name] = 2
    start_processing(conf, state)

def start_processing(conf, state):
    create_res_folder(conf.name, 0)
    process_iperf_res(conf, state)
    process_tcp_dump(conf, state)

def process_iperf_res(config:Config, state:State):
    """
    Reads all iperf results from all devices and writes the bandwidth into a single csv file
    """
    max_len = 0
    for dev_conf in config.dev_configs:
        max_len = max(max_len, dev_conf.length)
    res_txt = "" #f"Coarse bandwidth results for test {config.name} from the iperf measurements"
    
    #read data from all files
    mat = []
    cur = []
    for dev_conf in config.dev_configs:
        if state.dev_status[dev_conf.name] != 2: continue
        file_name = raw_res_fold + dev_conf.name + "_iperf_res.txt"
        try : f = open(file_name, mode='r')
        except FileNotFoundError: continue
        lines = f.readlines()
        reading = False
        for l in lines:
            tokens = l.split()
            if not tokens: continue
            if tokens[0] == "net.ipv4.tcp_congestion_control":
                if cur:
                    mat.append(cur)
                    cur = []
                cur.append(f"{dev_conf.name}  with cca {tokens[2]}")
            elif tokens[1] == "ID]": reading = not reading
            elif tokens[1] == "5]" and reading:
                num = float(tokens[6])
                unit = tokens[7]
                num = int(num * factor[unit[0]])
                cur.append(num)
            elif tokens[1] == "5]" and tokens[2] == "local":
                #line with connection info, extract port numbers
                port = int(tokens[5])
                dev_conf.src_ports.append(port)
        if cur: mat.append(cur)
        f.close()
        if delete_files_after_processing:
            os.remove(file_name)

    #rearrange data so that each test run is in a column instead of a row
    res_txt += f"\ntime"
    for j in range(len(mat)):
        res_txt += f",{mat[j][0]}"
    for i in range(max_len):
        res_txt += f"\n{i}s"
        for j in range(len(mat)):
            try: res_txt += f",{mat[j][i+1]}"
            except IndexError: pass

    res_file_name = f"{res_fold}iperf_res.csv"
    f = open(res_file_name, mode='w')
    f.write(res_txt.strip())
    f.close()
    

def process_tcp_dump(conf:Config, state:State):
    """
    Processes the tcpdump file of each device.
    """
    for dev_conf in conf.dev_configs:
        test_name = f"{conf.name}_{dev_conf.name}_"
        _, server_port = dev_conf.addr
        for i in range(dev_conf.number_of_cca):
            src_file = raw_res_fold + dev_conf.name + f"_dump_run{i}.pcap"
            src_port = dev_conf.src_ports[i]
            test_name_cca = test_name + dev_conf.ccas[i]
            res = process_pcap(src_file, test_name_cca, src_port, server_port)
            res_file_name = f"{res_fold}{test_name_cca}_tcp_analysis.csv"
            f = open(res_file_name, mode='w')
            f.write(res.strip())
            f.close()
            if delete_files_after_processing:
                os.remove(src_file)
            print(f"Processed {test_name_cca}")
        state.set_state(dev_conf.name, 3)
        print(f"Device {dev_conf.name} data has been processed")
            

def process_pcap(src_file:str, test_name:str, phone_port:int, server_port:int):
    """
    Processes the pcap file and returns the results as a string
    """

    stream_id = None
    i = 0
    res = f"{test_name}_Timestamp,{test_name}_throughput,{test_name}_avg_RTT,{test_name}_loss\n"
    #following variables store the old values during every intervall
    timestamp = -measuring_intervall
    ack_num = 0
    rtts = []
    pkt_num = 0
    num_retransmits = 0

    cap = pyshark.FileCapture(src_file)
    for pkt in cap:
        try:
            tcp = pkt.tcp
        except AttributeError:
            continue

        i += 1
        #if i > 20: break #early stopping point for debugging
        
        srcport = int(tcp.srcport)
        dstport = int(tcp.dstport)
        
        #filter out all packets that belong to another stream 
        if stream_id == None:
            #stream not yet identified
            if (srcport == phone_port and dstport == server_port) or (srcport == server_port and dstport == phone_port):
                #correct stream found
                stream_id = tcp.stream
            else:
                continue
                #print(srcport, dstport, phone_port, server_port)
        else:
            if not stream_id == tcp.stream:
                #packet belongs to other stream
                continue

        if srcport == server_port:
            #packet comes from server, analyse acks
            try:
                tcp.analysis_acks_frame #this field only exists if it is an acknowledgement packet
            except:
                continue
            
            rtt = float(tcp.analysis_ack_rtt)
            rtts.append(rtt)
            time_passed = float(tcp.time_relative) - timestamp
            if time_passed >= measuring_intervall:
                timestamp += measuring_intervall
                mod_time_passed = time_passed - measuring_intervall
                while mod_time_passed >= measuring_intervall:
                    #entering this loop means more than one intervall passed, the previous ones are zeroed
                    res += f"{timestamp},0,0,0\n"
                    timestamp += measuring_intervall
                    mod_time_passed -= measuring_intervall
                bytes_acked = int(tcp.ack) - ack_num
                throughput = bytes_acked / time_passed
                throughput_KBps = round(throughput/1000, 2)
                avg_rtt_ms = round(statistics.mean(rtts) * 1000, 2)
                try:
                    loss = round(float(num_retransmits) / pkt_num *100, 3)
                except ZeroDivisionError:
                    #No packets were send, i.e. no retransmissions or detected loss
                    loss = 0.0
                #print(f"Time: {tcp.time_relative}s, throughput: {throughput_KBps}KB/s, average RTT: {avg_rtt_ms}ms, loss: {loss}%\n")
                res += f"{timestamp},{throughput_KBps},{avg_rtt_ms},{loss}\n"

                #reset values for next period
                ack_num = int(tcp.ack)
                rtts = []
                pkt_num = 0
                num_retransmits = 0

        else:
            #packet goes to server, analyse retransmission
            pkt_num += 1
            try:
                tcp.analysis_retransmission
                num_retransmits += 1
            except:
                pass
        
    return res

def create_res_folder(name:str, i:int):
    """
    Creates the folder where all results will be saved. The name of the folder is a combination of the test configuration name and a number,
    such that multiple runs with the same configuration name don't override each other
    """
    dir = raw_res_fold + name + f"_{i}/"
    try:
        os.mkdir(dir)
        global res_fold
        res_fold = dir
    except OSError:
        create_res_folder(name, i+1)

if __name__ == "__main__":
    begin_processing_manual()