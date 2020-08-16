import shutil

from data_structures import Trace, Dev_config, Device
import iperf_server, server_frontend


"""
This file handles the conversion of traces to the required format.
To add a new handler, create a function in this file and add it to the handler_mapping in function init
"""
handler_mapping:dict = dict()
emulating_interval:int

def init():
    global handler_mapping, emulating_interval
    handler_mapping = {
        'txt': txt_loader,
        'interval': interval_loader,
        'norw': norw_loader,
    }
    emulating_interval = iperf_server.emulating_interval

def load_trace(source:str, trace_handler:str,):
    """
    Processes a trace with the given trace_handler and generates the corresponding Trace object
    arg source is a string with the name of the trace file
    """
    if (not source) or (not trace_handler):
        raise ValueError("No trace source or handler passed")
    func = handler_mapping[trace_handler]
    return func(source)

############################################## Write handlers below ##############################
"""
A trace hanlder should have following properties:
 - 1 argrument, the source file of the trace.
 - returns an object of type Trace, see data_structures.py
 - delays are in ms, loss in %, rate as a number with units (e.g. 10Gbps, 3Mbps, 1Kbps)
 - the handlers name in the handler_mapping (defined in init) should not be 'None'
"""

def txt_loader(src:str):
    """
    Simplest handler, just reads all the values from the file
    """
    f = open(src)
    delay = f.readline().strip().split(',')
    loss = f.readline().strip().split(',')
    rate = f.readline().strip().split(',')
    return Trace(delay, loss, rate)

def interval_loader(src:str):
    """
    Loads an interval file. First line is length of each interval in ms, following lines are values for each interval.
    Each interval should be a multiple of emulating_interval
    """
    f = open(src)
    intervals = f.readline().strip().split(',')
    delay = f.readline().strip().split(',')
    loss = f.readline().strip().split(',')
    rate = f.readline().strip().split(',')
    delay2 = []
    loss2 = []
    rate2 = []

    for i in range(len(intervals)):
        if emulating_interval > 0:
            num_of_reps = int(int(intervals[i])/emulating_interval)
        else:
            num_of_reps = int(intervals[i])
        for j in range(num_of_reps):
            delay2.append(delay[i])
            loss2.append(loss[i])
            rate2.append(rate[i])
    
    return Trace(delay2, loss2, rate2)

def norw_loader(src:str):
    if emulating_interval > 0:
        em_interval = emulating_interval
    else:
        em_interval = 1
    f = open(src)
    delay = [f.readline().strip()]
    loss = [f.readline().strip()]
    rate = []
    tokens = f.readline().strip().split(',')
    for t in tokens:
        try:
            interval = int(t.split()[0])
            bandwidth = t.split()[1]
            for i in range(int(interval/em_interval)):
                rate.append(bandwidth)
        except IndexError:
            pass #last token may be empty
    
    return Trace(delay, loss, rate)



############################################# functions for debugging #############################

def debug():
    """
    Initializes frontend so far to be able to open trace selection Frame
    """
    server_frontend.trace_worker.init()
    server_frontend.signal_queue = None
    server_frontend.init_tk()
    dev_conf = Dev_config("Mock_device", 10, False, None, None, "(1.1.1.1, 1024)", 1, ["CCA1"])
    device = Device(None, "(1.1.1.1, 1024)")
    server_frontend.Select_trace_frame(dev_conf, device, debug=True, ret_cmd=debug2)
    server_frontend.mainloop()

def debug2(device:Device, dev_conf:Dev_config):
    """
    Prints selection, loads trace 
    """
    trace_name = dev_conf.trace_name
    trace_handler = dev_conf.trace_handler
    print(f"Selected trace: {trace_name}\nSelected trace handler:{trace_handler}")
    if trace_name:
        trace = load_trace(trace_name, trace_handler)
        print(f"Delay:{trace.delay}\nLoss:{trace.loss}\nRate:{trace.rate}")
    else:
        print("No trace selected")
    server_frontend.shutdown()


if __name__ == "__main__":
    init()
    debug()