
class Device:
    socket = None
    addr:tuple
    name:str = "Not_initialized"
    ccas = []
    write_buff = []
    close_flag:bool = False

    def __init__(self, socket, addr):
        self.socket = socket
        self.addr = addr

class Config:
    name:str
    location:str
    num_of_dev:int
    dev_configs:list = [] #Dev_config list

    def __init__(self, name, location, num_of_dev, dev_list):
        self.name = name
        self.location = location
        self.num_of_dev = num_of_dev
        self.dev_configs = dev_list

    def copy(self):
        return Config(self.name, self.location, self.num_of_dev, self.dev_configs)

class Dev_config:
    name:str #name of the device
    length:int #length of the test
    rate:str #bandwidth limit in Mbps
    trace_name:str #name of the trace file
    trace_handler:str #name of the handler in trace_worker.py
    addr:tuple #address of the iperf server (ip, port)
    number_of_cca:int
    ccas:list #stringlist

    def __init__(self, dev_name, length, rate, trace_name, trace_handler, addr, num_cca, ccas):
        self.name = dev_name
        self.length = length
        self.rate = rate
        self.trace_name = trace_name
        self.trace_handler = trace_handler
        self.addr = addr
        self.number_of_cca = num_cca
        self.ccas = ccas
    
    def get_ip(self):
        ip, _ = self.addr
        return ip

class Server_settings:
    iperf_exec:str = "" #location of the iperf executable on the server
    network_dev:str = "" #name of the network device that will receive traffic
    ip:str = "" #ip address of the server
    #sudo_pw = None #sudo password required to set up netem, will not be saved

class Trace:
    delay:list
    loss:list
    rate:list

    def __init__(self, delay, loss, rate):
        self.delay = delay
        self.loss = loss
        self.rate = rate

    


