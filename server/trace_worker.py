import shutil


"""
This file handles the conversion of traces to the required format.
To add a new handler create a function in this file and add it to the handler_mapping in function init
"""
handler_mapping:dict = dict()

def init():
    global handler_mapping
    handler_mapping = {
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
 - returns 3 lists of strings, 1. delay list, 2. loss list, 3. rate list
 - delays are in ms, loss in %, rate as a number with units (e.g. 10Gbps, 3Mbps, 1Kbps)
"""