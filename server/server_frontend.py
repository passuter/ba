import time
import queue
from tkinter import *
from tkinter import filedialog
import socket

import server, iperf_server
from data_structures import *

#Queues for inter thread communication
config_queue:queue.Queue
device_queue:queue.Queue
signal_queue:queue.Queue

#global variables
root:Tk
active_config:Config = None
server_settings:Server_settings = Server_settings()
devices = []
index=-1 #index to store which device is currently selected. get the selected device with devices[index]

#global parameters
window_width = 600
window_height = 600
default_btn_width = 20

class Separator(Frame):
    def __init__(self, parent, height=10):
        Frame.__init__(self, parent, height=height)

class Back_to_home_btn(Button):
    def __init__(self, parent):
        Button.__init__(self, parent, text="BACK to HOME", fg="red")
        self["command"]=lambda: close_and_call(parent, home)

class Ok_btn(Button):
    def __init__(self, parent, cmd):
        Button.__init__(self, parent,text="OK", fg="green", command=cmd, width=default_btn_width)

class Back_btn(Button):
    def __init__(self, parent, cmd):
        Button.__init__(self, parent, text="CANCEL", fg="red", command=cmd, width=default_btn_width)

class Device_selection_lb(Listbox):
    """
    Lists all devices and one can select one device
    """
    def __init__(self, parent, return_cmd):
        Listbox.__init__(self, parent, selectmode=SINGLE)
        self.return_cmd = return_cmd
        self.parent = parent
        for d in devices:
            self.insert(END, d.name)
        self.bind('<<ListboxSelect>>', self.on_dev_select)
    
    def on_dev_select(self, evt):
        w = evt.widget
        try:
            global index
            index = w.curselection()[0]
            close_and_call(self.parent, lambda:select_dev(self.return_cmd)) #close parent and reload device selection window
        except IndexError: pass #if nothing is selected w.curselection()[0] fails

class Device_selection_frame(Frame):
    """
    Shows all connected devices and user can select one device.
    return_cmd specifies what to do after selection (i.e. after pressing CANCEL or OK)
    CANCEL does the same as OK but undoes the selection (i.e. setting global index to -1)
    """
    def __init__(self, parent, return_cmd):
        Frame.__init__(self, parent, width=window_width, height=window_height)
        bot_frame = Frame(self)
        btn_ok = Ok_btn(bot_frame, lambda: close_and_call(self, return_cmd))
        btn_cancel = Back_btn(bot_frame, lambda:self.back(return_cmd))
        btn_update = Button(self, text="UPDATE available devices", fg="blue")
        btn_update["command"] = lambda: close_and_call(self, lambda:call2(update_dev, lambda:select_dev(return_cmd)))
        select = Device_selection_lb(self, return_cmd)
        if index == -1:
            lbl = Label(self, text="Select a device to see information")
        else:
            dev = devices[index]
            lbl = Label(self, text=f"Name: {dev.name}\nAddress: {dev.addr}\nAvailable CCA: {dev.ccas}")

        btn_update.pack(side=TOP)
        bot_frame.pack(side=BOTTOM)
        btn_ok.pack(side=RIGHT)
        btn_cancel.pack(side=LEFT)
        select.pack(side=LEFT)
        lbl.pack(side=RIGHT)

    def back(self, return_cmd):
        global index
        index = -1 #returns without selecting anything
        close_and_call(self, return_cmd)

class Settings_frame(Frame):
    """
    Window which lets the user change the server settings
    """
    def __init__(self, parent):
        Frame.__init__(self, parent, width=window_width, height=window_height)
        self.pack(fill=BOTH)
        info = f"IP of this machine: {server_settings.ip}\nPort of this control server: {server.PORT}"
        top_lbl = Label(self, text="Change the configuration of the server")
        top_lbl.pack(side=TOP)
        info_lbl = Label(self, text=info)
        info_lbl.pack(side=TOP)
        container = Frame(self)
        iperf_lbl = Label(container, text=f"Iperf executable:\n{server_settings.iperf_exec}")
        iperf_lbl.grid(row=0, column=0)
        iperf_select = Button(container, text="Select", command=self.on_select)
        iperf_select.grid(row=0, column=1)
        sep1 = Separator(container, 20)
        sep1.grid(row=1)
        net_dev_lbl = Label(container, text="Network device (card) which will receive traffic (used for netem): ")
        net_dev_lbl.grid(row=2, column=0)
        self.net_dev_entry = Entry(container)
        self.net_dev_entry.insert(END, server_settings.network_dev)
        self.net_dev_entry.grid(row=2, column=1)
        container.pack(side=TOP)
        sep2 = Separator(self, 30)
        sep2.pack(side=TOP)
        back_btn = Back_btn(self, self.cancel)
        back_btn.pack(side=LEFT)
        ok_btn = Ok_btn(self, self.ok)
        ok_btn.pack(side=RIGHT)

    def on_select(self):
        loc = filedialog.askopenfilename(title="Select Iperf executable")
        if loc == '': return
        server_settings.iperf_exec = loc
        server_settings.network_dev = self.net_dev_entry.get()
        close_and_call(self, edit_settings)
    
    def ok(self):
        server_settings.network_dev = self.net_dev_entry.get()
        save_settings()
        close_and_call(self, home)

    def cancel(self):
        load_settings() #don't change settings, reload previous
        close_and_call(self, home)


class Home(Frame):
    """
    The main window
    """
    def __init__(self, parent):
        Frame.__init__(self, parent, width=window_width, height=window_height)
        self.pack(fill=BOTH)
        sep1 = Separator(self, 30)
        sep2 = Separator(self, 30)
        
        btn_view_dev = Button(self, text="See connected devices", fg="blue", height=2)
        btn_view_dev['command'] = lambda: close_and_call(self, lambda:select_dev(home))

        config_frame = Config_frame(self)

        button_quit = Button(self, text="QUIT", bg="red", height=2)
        button_quit['command'] = shutdown

        button_settings = Button(self, text="Server settings", command = lambda: close_and_call(self, edit_settings))

        btn_view_dev.pack(side=TOP, fill=X)
        config_frame.pack(side=TOP)
        sep1.pack(side=TOP)
        button_settings.pack(side=TOP)
        sep2.pack(side=TOP)
        button_quit.pack(side=BOTTOM, fill=X)


def home():
    """
    Creates the main window
    """
    Home(root)

    
def edit_settings():
   Settings_frame(root)

def select_dev(return_cmd):
    """
    Shows available devices and allows to select
    return_cmd specifies which function to call when the windows is closed
    """
    frame = Device_selection_frame(root, return_cmd)
    frame.pack(fill=BOTH)

def update_dev():
    """
    updates the devices list, deletes device selection
    """
    if not device_queue: return#when testing without active server (e.g. for testing), update_dev() fails as no queues exist
    signal_queue.put(2)
    try: dev:list = device_queue.get(timeout=3) #wait for server to fill queue
    except queue.Empty: print("Error: Unable to update devices")
    global devices, index
    index = -1 #reset device selection. Otherwise it might lead to an Index out of Bound error should some device(s) have disconnected
    devices = dev

def hi_foo(str):
    """
    This function creates a placeholder window with the str argument as text.
    str: string
    """
    frame = Frame(root)
    frame.pack(fill=BOTH)

    lbl = Label(frame, text=str)
    lbl.pack(side=TOP)

    btn = Back_to_home_btn(frame)
    btn.pack()

def close_and_call(to_close, foo):
    """
    Function that destroys the argument to_close & calls 2nd argument foo()
    """
    to_close.destroy()
    foo()

def shutdown():
    if signal_queue: signal_queue.put(1)
    save_settings()
    quit()

def call2(f1, f2):
    """
    Calls both functions f1 & f2
    """
    f1()
    f2()

def get_dev_by_name(dev_list:list, name):
    """
    Gets a dictionary from a list of dictionaries where the name field matches the second argument.
    Works with list of devices & list of device_configurations
    Returns None if not found
    """
    for d in dev_list:
        if d.name== name: return d
    return None 

def save_settings():
    """
    Save server settings to disk
    """
    f = open("server_settings.txt", 'w')
    txt = f"{server_settings.iperf_exec},{server_settings.network_dev}"
    f.write(txt)

def load_settings():
    """
    Load server settings
    """
    try:
        f = open("server_settings.txt", 'r')
        fields = f.readline().strip().split(",")
        server_settings.iperf_exec = fields[0]
        server_settings.network_dev = fields[1]
    except (FileNotFoundError):
        pass
    server_settings.ip = socket.gethostbyname(socket.gethostname()) #finds the ip address of the current machine


################################################################# below: deals with configurations######################################################################################################
class Config_frame(Frame):
    """
    Interface for choosing to select, run, add or modify a test configuration
    """
    def __init__(self, parent):
        Frame.__init__(self, parent, width=window_width, height=300)
        lbl1 = Label(self, text="selected configuration")
        if active_config == None: display_config = "None"
        else: display_config = active_config.name
        lbl2 = Label(self, text=display_config)

        mid_frame = Frame(self)
        btn_new_config = Button(mid_frame, text="Create new", width=15)
        btn_new_config['command']= lambda: close_and_call(parent, new_conf)
        btn_edit_config = Button(mid_frame, text="Edit current", width=15)
        btn_edit_config['command']= lambda: close_and_call(parent, mod_config)
        btn_sel_config = Button(mid_frame, text="Select existing", width=15)
        btn_sel_config['command']= lambda: close_and_call(parent, load_conf)

        sep = Separator(self)
        btn_run = Button(self, text="RUN this configuration", fg="green", width=default_btn_width)
        btn_run['command']= lambda: close_and_call(parent, start_run_config)


        lbl1.pack(side=TOP, fill=X)
        lbl2.pack(side=TOP, fill=X)
        mid_frame.pack()
        btn_new_config.pack(side=LEFT)
        btn_edit_config.pack(side=LEFT)
        btn_sel_config.pack(side=LEFT)
        sep.pack()
        btn_run.pack(side=BOTTOM)



class New_config_frame(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent)
        lbl = Label(self, text="Enter name of test configuration")
        self.e = Entry(self)
        btn = Button(self, text="Continue", fg="green")
        btn["command"]=self.ok
        back_btn = Back_to_home_btn(self)

        lbl.pack(side=TOP)
        self.e.pack()
        btn.pack(side=RIGHT)
        back_btn.pack(side=LEFT)

    def ok(self):
        conf_name= self.e.get()
        loc = filedialog.asksaveasfilename(title = "Save as", filetypes = (("text files","*.txt"),("all files","*.*")))
        if conf_name == '' or loc == '': return
        config = Config(conf_name, loc, 0, [])
        global active_config
        active_config = config
        close_and_call(self, lambda: mod_config())

class Mod_config_frame(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent)
        top_lbl = Label(self, text=f"Modify configuration \"{active_config.name}\"")
        server_config = Label(self, text="IMPROVE: change server configuration", height=6)
        
        
        self.lb = Listbox(self, selectmode=SINGLE)
        dev_confs = active_config.dev_configs
        for i in range(active_config.num_of_dev):
            self.lb.insert(END, dev_confs[i].name)
        self.lb.bind('<<ListboxSelect>>', self.on_dev_select)

        self.lbl = Label(self, text="No device selected")
        mod_btn = Button(self, text="Modify selected device", command=self.on_modify, width=default_btn_width)
        rm_btn = Button(self, text="Remove selected device", command=self.on_rm, width=default_btn_width)
        add_btn = Button(self, text="Add a new device", command=self.on_add, width=default_btn_width)
        separator = Separator(self)

        bot_frame = Frame(self)
        ok_btn = Ok_btn(bot_frame, lambda: close_and_call(self, home))
        save_btn = Button(bot_frame, text="SAVE", fg="green", command=save_conf, width=default_btn_width)
        ok_btn.pack(side=RIGHT)
        save_btn.pack(side=LEFT)

        top_lbl.pack(side=TOP)
        server_config.pack(side=TOP)
        bot_frame.pack(side=BOTTOM)
        separator.pack(side=BOTTOM)
        add_btn.pack(side=BOTTOM)
        rm_btn.pack(side=BOTTOM)
        mod_btn.pack(side=BOTTOM)
        self.lb.pack(side=LEFT)
        self.lbl.pack(side=RIGHT)
        
    def get_selected_dev(self):
        try: index = self.lb.curselection()[0]
        except IndexError: return None #if nothing is selected w.curselection()[0] fails
        name = self.lb.get(index)
        dev = None
        for d in active_config.dev_configs:
            if d.name == name:
                dev = d
                break
        return dev
    
    def on_dev_select(self, evt):
        dev_conf = self.get_selected_dev()
        if dev_conf == None: return

        count = 0 #counts number of CCAs displayed
        max_displ = 5
        text = f"Device Name: {dev_conf.name}\nRuntime: {dev_conf.length}s\nIperf Address: {dev_conf.addr}\nTrace: {dev_conf.trace}\nCCAs (shows maximal {max_displ}):"
        for cca in dev_conf.ccas:
            count += 1
            if count > max_displ: break
            text += f"\n{cca}"
        self.lbl['text'] = text
    
    def on_modify(self):
        dev_conf = self.get_selected_dev()
        if dev_conf == None: return
        device = get_dev_by_name(devices, dev_conf.name)
        if device == None: print(f"Cannot modifiy, {dev_conf.name} not connected")
        else: close_and_call(self, lambda:mod_dev_config(device, dev_conf))

    def on_add(self):
        close_and_call(self, lambda: add_dev_config1())

    def on_rm(self):
        dev_conf = self.get_selected_dev()
        if dev_conf == None: return
        active_config.dev_configs.remove(dev_conf)
        active_config.num_of_dev -= 1
        close_and_call(self, mod_config)

    
class Mod_dev_config_frame(Frame):
    def __init__(self, parent, device, device_config):
        Frame.__init__(self, parent)
        self.dev_name = device.name
        top_lbl = Label(self, text=f"Configuration: \"{active_config.name}\", Device: \"{self.dev_name}\"")
        bot_frame = Frame(self)
        btn_back = Back_btn(bot_frame, cmd=lambda: close_and_call(self,mod_config))
        btn_ok = Ok_btn(bot_frame, self.ok_action)

        #Frame to hold entry boxes to enter the config of the device
        #expose entries with self to functions in class
        lhs = Frame(self)
        length_lbl = Label(lhs, text="Enter length of test in seconds")
        length_lbl.grid(row=0, column=0)
        self.length_entry = Entry(lhs)
        self.length_entry.grid(row=0, column=1)
        self.length_entry.insert(END, device_config.length)
        trace_lbl = Label(lhs, text="Placeholder to select trace")
        trace_lbl.grid(row=1)
        ip, port = device_config.addr
        ip_lbl = Label(lhs, text="Enter ip of iperf server")
        ip_lbl.grid(row=2, column=0)
        self.ip_entry = Entry(lhs)
        self.ip_entry.grid(row=2, column=1)
        self.ip_entry.insert(END, ip)
        port_lbl = Label(lhs, text="Enter port of iperf server")
        port_lbl.grid(row=3, column=0)
        self.port_entry = Entry(lhs)
        self.port_entry.grid(row=3, column=1)
        self.port_entry.insert(END, port)


        #Frame to hold lisbox widget to select the CCAs
        rhs = Frame(self)
        cca_lbl = Label(rhs, text="Select CCA(s) to be used")
        cca_lbl.pack()
        self.lb = Listbox(rhs, selectmode=EXTENDED)
        self.lb.pack()
        for cca in device.ccas:
            self.lb.insert(END, cca)


        top_lbl.pack(side=TOP)
        bot_frame.pack(side=BOTTOM)
        lhs.pack(side=LEFT)
        rhs.pack(side=RIGHT)
        btn_back.pack(side=LEFT)
        btn_ok.pack(side=RIGHT)
    
    def ok_action(self):
        """
        Reads all values and checks if they are sensible and result in a correct device configuration
        """
        correct_values = True
        try: length = int(self.length_entry.get())
        except ValueError: print("Invalid entry for length, must be a single integer strictly larger than 0"); correct_values = False    
        ip = self.ip_entry.get()
        try: port = int(self.port_entry.get())
        except ValueError: print("Invalid entry for port, must be a single integer"); correct_values = False
        indices = self.lb.curselection()
        ccas = []
        for i in indices:
            ccas.append(self.lb.get(i))
        
        if correct_values:
            dev_config = Dev_config(self.dev_name, length, "default", (ip, port), len(ccas), ccas)
            if is_valid_dev_config(dev_config, print_error=print): self.ok(dev_config)
            else: pass #some entry was invalid, nothing to do
        else: pass #some entry was invalid, nothing to do

    def ok(self, dev_conf):
        """
        Adds the dev_conf to the currently active configuration (removes duplicates if necessary)
        """
        #remove duplicate
        for d in active_config.dev_configs:
            if d.name == dev_conf.name:
                active_config.dev_configs.remove(d)
                active_config.num_of_dev -= 1
        
        #add dev_conf
        active_config.dev_configs.append(dev_conf)
        active_config.num_of_dev += 1
        close_and_call(self, mod_config)

class Run_config_frame(Frame):
    def __init__(self, parent, state:State):
        Frame.__init__(self, parent, width=window_width, height=window_height)
        self.pack(fill=BOTH)
        self.state = state
        #TODO report setup progression

        bot_frame = Frame(self)
        bot_frame.pack(side=BOTTOM)
        back_btn = Back_btn(bot_frame, lambda: close_and_call(self, home))
        back_btn.pack(side=LEFT)
        run_btn = Button(bot_frame, text="RUN", fg="green", command=self.run_conf, width=default_btn_width)
        run_btn.pack(side=RIGHT)
        
    def run_conf(self):
        config_queue.put(active_config.copy())
        close_and_call(self, lambda: hi_foo(f"Running test \"{active_config.name}\""))
    
class Ask_sudo_frame(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent, width=window_width, height=window_height)
        self.pack(fill=BOTH)
        top_lbl = Label(self, text=f"Enter sudo password.\nIt is needed to automatically setup netem.")
        top_lbl.pack(side=TOP)
        self.entry = Entry(self)
        self.entry.pack(side=TOP)
        bot_frame = Frame(self)
        bot_frame.pack(side=BOTTOM)
        cont_btn = Button(bot_frame, text="Continue without sudo", command=self.without, width=default_btn_width)
        cont_btn.pack(side=TOP)
        back_btn = Back_btn(bot_frame, lambda: close_and_call(self, home))
        back_btn.pack(side=LEFT)
        ok_btn = Ok_btn(bot_frame, self.ok)
        ok_btn.pack(side=RIGHT)
    
    def ok(self):
        password = self.entry.get()
        if password == '':
            return
        else:
            server_settings.sudo_pw = password
            close_and_call(self, run_config)

    def without(self):
        server_settings.sudo_pw = None
        close_and_call(self, run_config)


def new_conf():
    """
    Ask for name & location of a new configuration
    """
    frame = New_config_frame(root)
    frame.pack()

def mod_config():
    """
    Modify the selected config
    """
    if active_config == None: home()
    else:
        frame = Mod_config_frame(root)
        frame.pack()

def mod_dev_config(device, device_config):
    """
    Modify the configuration for a device dev
    """
    frame = Mod_dev_config_frame(root, device, device_config)
    frame.pack()

def add_dev_config1():
    """
    First part of selecting a new device for which to add a test configuration & open modify.
    Updates the devices list & calls the selection function.
    """
    update_dev() 
    select_dev(add_dev_config2)

def add_dev_config2():    
    """
    Second part of selecting a new device for which to add a test configuration & open modify.
    Creates an new, empty configuration for the selected device and calls 
    """
    if index == -1: mod_config() #no device selected, return to modify configuration screen
    else:
        dev = devices[index]
        conf = Dev_config(dev.name, 0, 'none', ('0.0.0.0', 0), 0, [])
        mod_dev_config(dev, conf)

def start_run_config():
    """
    Called when user clicks on 'Run this configuration' on the home window.
    Checks if the configuration is valid and then prompts for sudo password or goes to run_config
    """
    if is_valid_config(print_error=print):
        if server_settings.sudo_pw == None:
            Ask_sudo_frame(root)
        else:
            run_config()
    else:
        home() #cannot run invalid configuration

def run_config(state=None):
    """
    This function tries to setup the iperf server.
    state holds all values about the currrent progress of the setup
    """
    state = iperf_server.setup(state)
    #TODO try to set up server
    Run_config_frame(root, state)

def save_conf():
    """
    Writes the current configuration to a file
    """
    f = open(active_config.location, 'w')
    #txt = f"{active_config['name']}, Version 1\nServer_settings:tbd\nNumber_of_devices: {active_config['num_of_dev']}\n"
    txt = f"{active_config.name}, Version 2\nNumber_of_devices: {active_config.num_of_dev}\n"
    for d in active_config.dev_configs:
        txt += dev_conf_to_str(d) + f"\n"
    f.write(txt)

def dev_conf_to_str(dev_conf:Dev_config):
    """
    Writes the device configuration into a string (ends it with newline)
    """
    ip, port = dev_conf.addr
    txt = f"{dev_conf.name},{dev_conf.length},{dev_conf.trace},{ip},{port},{dev_conf.number_of_cca}"
    for cca in dev_conf.ccas:
        txt +=f",{cca}"
    return txt


def load_conf():
    """
    Asks for a configuration to open and puts it into active_config.
    """
    f_loc = filedialog.askopenfilename(title = "Select file", filetypes = (("text files","*.txt"),("all files","*.*")))
    if f_loc == '': home() #no file was selected
    else:
        f = open(f_loc, mode='r')
        line_1 = f.readline().split(',')
        try:
            name, version = line_1[0], int(line_1[1].split()[1]) #reads name & version number of the configuration file
            version_handlers = {
                1: lambda: load_v1(f, name, f_loc),
                2: lambda: load_v2(f, name, f_loc),
            }
            try: version_handlers[version]() #calls the handler belonging to the version number
            except KeyError: 
                print("Invalid configuration version")
        except IndexError: print("Could not load configuration, reading of name and version failed")
        home()

#load_v* load a specific version
def load_v1(f, name, f_loc):
    #used to load older files
    server_sett = f.readline() #reads the serversettings, deprecated
    num_of_dev = int(f.readline().split()[1])
    dev_list = []
    for i in range(num_of_dev):
        l = f.readline()
        if l == '': #file ended early
            print("Configuration file corrupted: Less devices than specified")
            home()
        l = l.rstrip().split(',') #remove tailing newline & split by ','
        dev_name = l[0]
        length = int(l[1])
        trace = l[2]
        addr = (l[3], int(l[4]))
        num_cca = int(l[5])
        ccas = []
        for j in range(num_cca):
            ccas.append(l[6+j])
        dev_conf = Dev_config(dev_name, length, trace, addr, num_cca, ccas)
        dev_list.append(dev_conf)
    conf = Config(name, f_loc, num_of_dev, dev_list)
    global active_config
    active_config = conf

def load_v2(f, name, f_loc):
    num_of_dev = int(f.readline().split()[1])
    dev_list = []
    for i in range(num_of_dev):
        l = f.readline()
        if l == '': #file ended early
            print("Configuration file corrupted: Less devices than specified")
            home()
        l = l.rstrip().split(',') #remove tailing newline & split by ','
        dev_name = l[0]
        length = int(l[1])
        trace = l[2]
        addr = (l[3], int(l[4]))
        num_cca = int(l[5])
        ccas = []
        for j in range(num_cca):
            ccas.append(l[6+j])
        dev_conf = Dev_config(dev_name, length, trace, addr, num_cca, ccas)
        dev_list.append(dev_conf)
    conf = Config(name, f_loc, num_of_dev, dev_list)
    global active_config
    active_config = conf

def is_valid_config(print_error=None):
    """
    Checks wheter the current configuration is a valid configuration.
    Argument print_error should be a function with an string list argument, which will output the reason(s) if it is invalid.
    """
    if active_config == None:
        print_error(["No configuration selected"])
        return False
    correct_values = True #Set to false if any value does not meet criterea
    error_txt = [f"Invalid configuration \"{active_config.name}\""]
    if active_config.name == "":
        correct_values = False
        error_txt.append(f"Invalid configuration name")
    num_dev = len(active_config.dev_configs)
    if num_dev != active_config.num_of_dev:
        correct_values = False
        error_txt.append("Length of dev_configs list and num_of_dev don't correspond (Internal error)")
    if num_dev <= 0:
        correct_values = False
        error_txt.append("No device in this test")
    for d in active_config.dev_configs:
        correct_values = is_valid_dev_config(d, error_txt.append) and correct_values
    
    #check if device is connected and has all specified CCAs
    update_dev()
    for dev_conf in active_config.dev_configs:
        name = dev_conf.name
        device = get_dev_by_name(devices, name)
        if get_dev_by_name(devices, name) == None:
            correct_values = False
            error_txt.append(f"Device \"{name}\" is not connected")
        else :
            for cca in dev_conf.ccas:
                if cca not in device.ccas:
                    correct_values = False
                    error_txt.append(f"Device \"{name}\" has no CCA \"{cca}\"")

    if (not correct_values) and print_error:
        print_error(error_txt)
    return correct_values

def is_valid_dev_config(dev_config:Dev_config, print_error=None):
    """
    Checks wheter a given device configuration is a valid device configuration.
    Argument print_error should be a function with an string list argument, which will output the reason(s) if it is invalid.
    """
    correct_values = True #Set to false if any value does not meet criterea
    error_txt = [f"Invalid device configuration for {dev_config.name}"]
    if dev_config.length <= 0: error_txt.append(f"Invalid length, must be strictly larger than 0, is {dev_config.length}"); correct_values = False
    correct_values = is_valid_addr(dev_config.addr, lambda str: error_txt.append(str)) and correct_values
    num_cca = len(dev_config.ccas)
    if num_cca != dev_config.number_of_cca:
        correct_values = False
        error_txt.append("Number of selected CCAs is not the same as specified number")
    if num_cca <= 0:
        correct_values = False
        error_txt.append(f"Number of selected CCAs: {num_cca}, must be strictly larger than 0")
    
    if (not correct_values) and print_error:
        print_error(error_txt)
    return correct_values

def is_valid_addr(addr:tuple, print_error=None):
    """
    Checks wheter a given addr is a valid address.
    Argument print_error should be a function with an string argument, which will output the reason if it is invalid.
    """
    valid = True
    ip, port = addr
    try:
        socket.inet_aton(ip)
    except OSError:
        valid = False
        if print_error: print_error("Given ip address is not valid")
    max_port = 65535
    if not (port >= 0 and port < max_port):
        valid = False
        if print_error: print_error(f"Port range is invalid, must be between 0 (inclusive) and {max_port}")
    return valid
        
##################################### main function####################################################################################################################################################
def main(conf_queue:queue.Queue, dvice_queue:queue.Queue, signl_queue:queue.Queue):
    global config_queue, device_queue, signal_queue, root
    root = Tk()
    root.geometry("500x500")
    root.title("Control server")
    config_queue = conf_queue
    device_queue = dvice_queue
    signal_queue = signl_queue
    root.protocol("WM_DELETE_WINDOW", shutdown) #closing the window also triggers a shutdown of the server
    load_settings()
    home()
    #test()
    mainloop()

if __name__ == "__main__":
    main(None, None, None)