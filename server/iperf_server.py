import subprocess
import os
import shutil
import threading
import multiprocessing
from time import sleep

import server_frontend
import trace_worker
from data_structures import *

#Global variables
print_error = print #global function for printing errors
tmp_dir = "tmp/"
traces:dict = dict() #mapping of traces files to Trace objects
netem_thread = None
iperf_processes = []
running = False

def setup():
    """
    This function prepares the iperf server
    Returns True if it succeeded and False otherwise
    """
    try: os.mkdir(tmp_dir) #create new temporary directory
    except OSError:
        print_error(["Could not create tmp directory"])
        return False
    #Check if the shell can execute commands
    try:
        #p = subprocess.Popen(['echo hello'], stdout=subprocess.PIPE, stderr = subprocess.STDOUT)
        #out, err = p.communicate()
        out = execute("echo hello")
        if out != 'hello':
            print(f"Shell error, got {out}")
            return False
    except FileNotFoundError:
        print(f"Shell error, FileNotFound")
        return False

    generate_traces()
    start_iperf_processes()
    netem_cmds, flow_maps = generate_netem_cmd()
    if netem_cmds != None:
        global netem_thread
        netem_thread = threading.Thread(target=netem_emulator, args=[flow_maps])
        out = execute_multiple(netem_cmds)
        print(out)
    return True

def start_emulating():
    global running
    running = True
    if netem_thread != None:
        netem_thread.start()

def stop_emulating():
    global running
    running = False
    if netem_thread != None:
        netem_thread.join(5)
    
    
def netem_emulator(flow_mappings):
    """
    Changes the netem values according to the traces continuously
    """
    i = 0
    #print(flow_mappings)
    net_dev = server_frontend.server_settings.network_dev
    while running:
        for (trace_name, flowid) in flow_mappings:
            trace = traces[trace_name]
            handleid = flowid[3:5]
            delay = trace.delay[i % (len(trace.delay))]
            loss = trace.loss[i % (len(trace.loss))]
            rate = trace.rate[i % (len(trace.rate))]
            cmd = f"sudo tc qdisc change dev {net_dev} parent {flowid} handle {handleid}: netem delay {delay} "
            if loss != 0: cmd +=f"loss {loss}% "
            cmd += f"rate {rate}"
            out = execute(cmd)
            if out != '':
                print(cmd)
                print(out)
        i += 1
        sleep(0.01) #wait for 10ms before changing again


def execute(cmd, with_error=False):
    """
    Executes 1 command on the shell, returns the output
    """
    input = cmd.split()
    p = subprocess.Popen(input, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout, stderr = p.communicate()
    if (with_error):
        stdout += f"\n{stderr}"
    return stdout.decode("utf-8").strip()

def execute_multiple(cmds:list, with_error=False):
    out = ""
    for cmd in cmds:
        out += execute(cmd, with_error) + f"\n"
    return out


def generate_netem_cmd():
    """
    Generates shell commands to setup netem.
    Returns the commands or None if no trace has been selected and a mapping of trace_names & flow_ids
    """
    dev_configs = server_frontend.active_config.dev_configs
    worklist = [] #list of device configs with a trace
    for d in dev_configs:
        if d.trace_name != None:
            worklist.append(d)

    #Check wheter any device for this machine has a loss trace. If not, return None
    if not worklist:
        return None, None

    network_dev = "eth0" #default ethernet
    if server_frontend.server_settings.network_dev != "":
        network_dev = server_frontend.server_settings.network_dev
    #replace default root qdisc 
    cmds = [f"sudo tc qdisc add dev {network_dev} handle 1: root htb"]
    
    id_mapping = []
    i = 0
    for d in worklist:
        if i < 10: flow_id = f"1:10{i}"
        else: flow_id = f"1:1{i}"
        handleid = flow_id[3:5]
        #add a class for each device and limit it to a high default value
        cmds.append(f"sudo tc class add dev {network_dev} parent 1: classid {flow_id} htb rate 10Gbps") #set max value
        #add a def values for that class
        cmds.append(f"sudo tc qdisc add dev {network_dev} parent {flow_id} handle {handleid}: netem delay 0 rate 10Gbps")
        #add a filter to match this device with the class
        device_ip, _ = server_frontend.get_dev_by_name(server_frontend.devices, d.name).addr
        cmds.append(f"sudo tc filter add dev {network_dev} parent 1: protocol ip prio 1 u32 match ip dst {device_ip}/32 flowid {flow_id}")
        id_mapping.append((d.trace_name, flow_id))
        #print(id_mapping)

    return cmds, id_mapping

def start_iperf_processes():
    iperf_exe = server_frontend.server_settings.iperf_exec
    for dev_config in server_frontend.active_config.dev_configs:
        _, port = dev_config.addr
        p = multiprocessing.Process(target=run_iperf, args=(port, iperf_exe))
        iperf_processes.append(p)
        p.start()

def run_iperf(port, iperf_cmd):
    cmd = f"{iperf_cmd} -s -p {port}"
    execute(cmd)

def generate_traces():
    for dev_config in server_frontend.active_config.dev_configs:
        if dev_config.trace_name in traces:
            continue # trace has been converted already
        else:
            trace = trace_worker.convert_trace(dev_config.trace_name, dev_config.trace_handler)
            traces[dev_config.trace_name] = trace


def clear_setup():
    """
    Resets the setup of the iperf server. This should be called always when the active configuration changes to avoid inconsistency during the setup
    """
    try: shutil.rmtree(tmp_dir) #delete all temporary files
    except OSError: pass #print_error(["Error when deleting tmp dir"]) #debug only
    global netem_thread, traces, running
    netem_thread = None
    #remove the rules again
    execute(f"sudo tc qdisc del dev {server_frontend.server_settings.network_dev} handle 1: root htb")
    while iperf_processes:
        p = iperf_processes.pop()
        p.terminate()
    traces = dict()
    running = False