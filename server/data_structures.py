
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
    name:str
    length:int
    trace:str
    addr:tuple
    number_of_cca:int
    ccas:list #stringlist

    def __init__(self, dev_name, length, trace, addr, num_cca, ccas):
        self.name = dev_name
        self.length = length
        self.trace = trace
        self.addr = addr
        self.number_of_cca = num_cca
        self.ccas = ccas

class State:
    shell_works:bool = False
    sudo_pw:str = False
    wants_sudo:bool = False
    has_sudo:bool = False
    machines:list = [] #Machine list

class Server_settings:
    iperf_exec:str = "" #location of the iperf executable on the server
    network_dev:str = "" #name of the network device that will receive traffic
    ip:str = "" #ip address of the server
    sudo_pw = None #sudo password required to set up netem, will not be saved

class Machine:
    pass

    


