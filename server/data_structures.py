from os import path

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
    trace_name:str #name of the trace file
    trace_handler:str #name of the handler in trace_worker.py
    addr:tuple #address of the iperf server (ip, port)
    src_ports:list #ports of the phone during iperf transmissions, used only in processing
    number_of_cca:int
    ccas:list #stringlist
    #src_ports and ccas should never be reordered, as they will be matched by order during
    #processing

    def __init__(self, dev_name, length, trace_name, trace_handler, addr, num_cca, ccas):
        self.name = dev_name
        self.length = length
        self.trace_name = trace_name
        self.trace_handler = trace_handler
        self.addr = addr
        self.number_of_cca = num_cca
        self.ccas = ccas
        self.src_ports = []
    
    def get_ip(self):
        ip, _ = self.addr
        return ip

    def get_trace_name(self):
        if self.trace_name == None: return "None"
        else:
            _, trace_file_name = path.split(self.trace_name)
            return trace_file_name

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

class State:
    started:bool = False
    pull_complete:bool = False
    finished:bool = False
    config_name:str
    #maps a device to a status
    dev_status:dict = dict() 
    status:dict = {
        0: "running",
        1: "finished run, now pulling data",
        2: "data pulled, now processing",
        3: "data processed"
    }

    def __init__(self, config:Config):
        self.config_name = config.name
        for d in config.dev_configs:
            self.dev_status[d.name] = 0

    def all_finished_stage(self, i:int):
        """
        Returns true if all devices have finished the stage i
        """
        run_complete = True
        for d in self.dev_status:
            if self.dev_status[d] <= i:
                run_complete = False
        return run_complete

    def set_state(self, name:str, i:int):
        """
        Set state of device to i
        """
        self.dev_status[name] = i
        if self.all_finished_stage(2):
            self.finished = True

    def print_status(self):
        """
        Returns this state as a string
        """
        if not self.started:
            return "Test has not yet started"
        else:
            txt = ""
            for name in self.dev_status:
                txt += f"{name}: {self.status[self.dev_status[name]]}\n"
        if self.finished:
            txt += "Test has finished"
        return txt
        

