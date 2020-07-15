import shutil

from data_structures import Trace


"""
This file handles the conversion of traces to the required format.
To add a new handler create a function in this file and add it to the handler_mapping in function init
"""
handler_mapping:dict = dict()

def init():
    global handler_mapping
    handler_mapping = {
        'txt': txt_loader,
    }

def convert_trace(source:str, trace_handler:str,):
    """
    Processes a trace with the given trace_handler and generates the corresponding lists
    arg source is a string with the name of the trace file
    """
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