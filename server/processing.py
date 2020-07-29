import os

import server_frontend, server
from data_structures import *

raw_res_fold = server.results_folder + "/"
res_fold:str = ""

factor = {
    "b": 1,
    "K": 1000,
    "M": 10**6,
    "G": 10**9,
}

def begin_processing():
    conf = server_frontend.active_config
    state = server_frontend.state
    create_res_folder(conf.name, 0)
    process_iperf_res(conf, state)


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
                if cur: mat.append(cur)
                cur.append(f"{dev_conf.name}  with cca {tokens[2]}")
            elif tokens[1] == "ID]": reading = not reading
            elif tokens[1] == "5]" and reading:
                num = float(tokens[6])
                unit = tokens[7]
                num = int(num * factor[unit[0]])
                cur.append(num)
        if cur: mat.append(cur)
        f.close()
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
    

def process_tcp_dump():
    pass #TODO

def create_res_folder(name:str, i:int):
    dir = raw_res_fold + name + f"_{i}/"
    try:
        os.mkdir(dir)
        global res_fold
        res_fold = dir
    except OSError:
        create_res_folder(name, i+1)

if __name__ == "__main__":
    #load config and state for debugging
    dev_conf = Dev_config("Redmi4A", 3, "/home/suter/Documents/ba/git/ba/loss_traces/high_loss.txt", "txt", ("192.168.1.127",5201), 1, "cubic")
    server_frontend.active_config = Config("test_fast", "", 1, [dev_conf])
    server_frontend.state = State(server_frontend.active_config)
    server_frontend.state.started = True
    server_frontend.state.pull_complete = True
    server_frontend.state.dev_status["Redmi4A"] = 2
    begin_processing()