import os
import pyshark
import statistics
import threading
import sys
from tkinter import filedialog

import server_frontend, server, iperf_server
from data_structures import *

raw_res_fold:str
res_fold:str = ""
delete_files_after_processing:bool

measuring_interval = 0.25 #in seconds

def init():
    """
    Initializes global variables
    """
    global raw_res_fold, delete_files_after_processing
    delete_files_after_processing = True #if False, raw data (.pcap files etc) will be kept
    #However, running a test might override those files
    raw_res_fold = server.results_folder + "/"

factor = {
    "b": 1,
    "K": 1000,
    "M": 10**6,
    "G": 10**9,
}

def empty_tcp_line(timestamp, separator):
    """
    Helper function to create an entry for tcp analysis should no data be available
    """
    return f"{timestamp},0,0,0{separator}"

def begin_processing(): 
    """
    Starts the processing of the data
    """
    state, conf = server_frontend.run_state_configs[server_frontend.run_number]
    process(conf, state)
    #threading.Thread(target=process, args=(conf, state)).start() #process on a different thread to not busy the server, but crashes

def begin_processing_manual():
    """
    Starts the processing of the data manually (i.e. without running the server)
    """
    init()
    args = sys.argv
    for arg in args:
        if arg == '-no_del' or arg == '-nodel' or arg == '-no_delete' or arg == '-nodelete':
            global delete_files_after_processing
            delete_files_after_processing = True
            print("Not deleting files")
        elif arg == '-combine' or arg == '-comb':
            combine(args)
            return

    conf = server_frontend.load_conf()
    if not conf:
        print("No configuration selected")
        return
    state = State(conf)
    state.started = True
    state.pull_complete = True
    for dev_conf in conf.dev_configs:
        state.dev_status[dev_conf.name] = 2
    process(conf, state)

def process(conf, state):
    create_res_folder(conf.name, 0)
    process_iperf_res(conf, state)
    process_tcp_dump(conf, state)
    process_battery_results(conf, state)
    if delete_files_after_processing:
        try:
            os.remove(raw_res_fold + "res_id.txt")
        except:
            pass
    print(f"Finished processing data for test {conf.name}")
    iperf_server.clear_setup()
    if server_frontend.run_number < len(server_frontend.run_state_configs)-1:
        #not last test, start next test run
        server_frontend.run_number += 1
        server_frontend.run_conf()
    else:
        print(f"All done\n\n")



def process_iperf_res(config:Config, state:State):
    """
    Reads all iperf results from all devices and writes the bandwidth into a single csv file
    Throughput in bits/second
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
                cur.append(f"timestamp,{dev_conf.name} with cca {tokens[2]}")
            elif tokens[1] == "ID]": reading = not reading
            elif tokens[1] == "5]" and reading:
                timestamp = tokens[2]
                num = float(tokens[6])
                unit = tokens[7]
                num = int(num * factor[unit[0]])
                cur.append(f"{timestamp},{num}")
            elif tokens[1] == "5]" and tokens[2] == "local":
                #line with connection info, extract port numbers
                port = int(tokens[5])
                dev_conf.src_ports.append(port)
        if cur:
            mat.append(cur)
        f.close()
        if delete_files_after_processing:
            os.remove(file_name)

    #rearrange data so that each test run is in a column instead of a row
    #res_txt += f"\ntime"
    for j in range(len(mat)):
        res_txt += f"{mat[j][0]},"
    for i in range(max_len):
        #res_txt += f"\n{i}s"
        res_txt += f"\n"
        for j in range(len(mat)):
            try: res_txt += f"{mat[j][i+1]},"
            except IndexError: pass#res_text += f"0,0"

    res_file_name = f"{res_fold}iperf_res.csv"
    f = open(res_file_name, mode='w')
    f.write(res_txt.strip())
    f.close()
    

def process_tcp_dump(conf:Config, state:State):
    """
    Processes the tcpdump file of each device.
    Throughput in KBps
    """
    processed_files = []
    for dev_conf in conf.dev_configs:
        if dev_conf.is_battery_test:
            continue #a battery test has no tcp dump files
        test_name = f"{conf.name}_{dev_conf.name}_"
        _, server_port = dev_conf.addr
        if not dev_conf.number_of_cca == len(dev_conf.src_ports):
            #number of ports and number of ccas do not match, cannot process this device
            #can happen for example if phone could not connect to iperf server, then the iperf file cannot be read completely
            state.set_state(dev_conf.name, -1)
            print(f"Error in process_tcp_dump for {dev_conf.name}")
            print(len(dev_conf.src_ports))
            continue
        for i in range(dev_conf.number_of_cca):
            src_file = raw_res_fold + dev_conf.name + f"_dump_run{i}.pcap"
            src_port = dev_conf.src_ports[i]
            test_name_cca = test_name + dev_conf.ccas[i]
            res = process_pcap(src_file, test_name_cca, src_port, server_port)
            res_file_name = f"{res_fold}{test_name_cca}_tcp_analysis.csv"
            f = open(res_file_name, mode='w')
            f.write(res.strip())
            f.close()
            processed_files.append(res_file_name)
            if delete_files_after_processing:
                os.remove(src_file)
            print(f"Processed {test_name_cca}")
        state.set_state(dev_conf.name, 3)
        dev_conf.src_ports = [] #reset src_ports, necessary if running multiple test with same configuration
        #print(f"Device {dev_conf.name} data has been processed")
    combined_output = f"{res_fold}{conf.name}_combined.csv"
    combine_files(processed_files, combined_output)


def process_pcap(src_file:str, test_name:str, phone_port:int, server_port:int):
    """
    Processes the pcap file and returns the results as a string
    """

    stream_id = None
    i = 0
    res = f"{test_name}_Timestamp,{test_name}_throughput,{test_name}_avg_RTT,{test_name}_loss,\n"
    #following variables store the old values during every interval
    timestamp = -measuring_interval
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
            if time_passed >= measuring_interval:
                timestamp += measuring_interval
                mod_time_passed = time_passed - measuring_interval
                while mod_time_passed >= measuring_interval:
                    #entering this loop means more than one interval passed, the previous ones are zeroed
                    res += empty_tcp_line(timestamp, f",\n")
                    timestamp += measuring_interval
                    mod_time_passed -= measuring_interval
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
                res += f"{round(timestamp, 4)},{throughput_KBps},{avg_rtt_ms},{loss},\n"

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


def process_battery_results(conf:Config, state:State):
    """
    Processes the battery result files
    """
    #read results from file into accumulator
    res = [] #accumulator for results
    for dev_conf in conf.dev_configs:
        if not dev_conf.is_battery_test:
            continue #only process battery tests
        test_name = f"{conf.name}_{dev_conf.name}_"
        for i in range(dev_conf.number_of_cca):
            src_file = f"{raw_res_fold}{dev_conf.name}_battery_run{i}.txt"
            test_name_cca = test_name + dev_conf.ccas[i]
            f = open(src_file, mode="r")
            res.append(process_battery_file(f, test_name_cca))
            f.close()
            if delete_files_after_processing:
                os.remove(src_file)
        state.set_state(dev_conf.name, 3)
        
    #combine & write results
    max_lines = 0
    for lines in res:
        max_lines = max(max_lines, len(lines))
    
    res_txt = ""
    for i in range(max_lines):
        for j in range(len(res)):
            try:
                res_txt += res[j][i]
            except IndexError:
                #Some test might have different length, add all zeros
                res_txt += "0,0,0,"
        res_txt += f"\n"
    dst_file = f"{res_fold}{conf.name}_battery_results.csv"
    out = open(dst_file, mode="w")
    out.write(res_txt)
    out.close()

def process_battery_file(f, test_name_cca):
    res = []
    res.append(f"{test_name_cca}_timestamp,{test_name_cca}_battery_pct,{test_name_cca}_battery_charging,")
    lines = f.readlines()
    for l in lines:
        res.append(l.strip())
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

def combine(args):
    """
    Helper function that combines results from different runs into a single file (tcpdump results only)
    """
    file_names = []
    file_names_reading = False
    output_name = ""
    output_name_reading = False

    for arg in args:
        if arg == "-combine" or arg == "-comb":
            file_names_reading = True
            output_name_reading = False
        elif arg == "-out":
            output_name_reading = True
            file_names_reading = False
        elif file_names_reading:
            file_names.append(arg)
        elif output_name_reading:
            output_name = arg
    
    if not file_names: return
    if output_name == "":
        output_name = raw_res_fold + "combine_tmp.txt"
    combine_files(file_names, output_name)


def combine_files(file_names, output_name):
    input = []
    max_lines = -1
    for name in file_names:
        f = open(name, mode='r')
        lines = f.readlines()
        max_lines = max(max_lines, len(lines))
        input.append(lines)

    res = ""
    for i in range(max_lines):
        for lines in input:
            try:
                l = lines[i].strip()
                res += l
            except IndexError:
                timestamp = (i-1) * measuring_interval
                res += empty_tcp_line(timestamp, ",")
        res += f"\n"
    
    f = open(output_name, mode='w')
    f.write(res)
    f.close()



if __name__ == "__main__":
    begin_processing_manual()