import time
import queue
from tkinter import *
from tkinter import filedialog
from datetime import datetime
import socket

import server, iperf_server, trace_worker
from data_structures import *

#Queues for inter thread communication
config_queue:queue.Queue
device_queue:queue.Queue
signal_queue:queue.Queue

#global variables
root:Tk
active_config:Config = None
run_state_configs:list = list()
run_number = 0
server_settings:Server_settings = Server_settings()
devices = []
index=-1 #index to store which device is currently selected. get the selected device with devices[index]

#global parameters
window_width = 600
window_height = 600
default_btn_width = 20
print_error = print #global function for reporting errors, used to implement better error reporting

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
        iperf_lbl = Label(container, text=f"Command to run iperf:\n{server_settings.iperf_exec}")
        iperf_lbl.grid(row=0, column=0)
        self.iperf_entry = Entry(container)
        self.iperf_entry.insert(END, server_settings.iperf_exec)
        self.iperf_entry.grid(row=0, column=1)
        sep1 = Separator(container, 20)
        sep1.grid(row=1)
        net_dev_lbl = Label(container, text=f"Network device (card) which will\nreceive traffic (used for netem):")
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
        if loc == '' or loc == (): return
        server_settings.iperf_exec = loc
        server_settings.network_dev = self.net_dev_entry.get()
        close_and_call(self, edit_settings)
    
    def ok(self):
        server_settings.iperf_exec = self.iperf_entry.get().strip()
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
    clear_run_setup()
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
        if d.name == name: return d
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
    Interface for choosing to select, run, add or modify a test configuration on the home window
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
        btn_sel_config['command']= lambda: close_and_call(parent, activate_conf)

        sep1 = Separator(self)
        sep2 = Separator(self)
        btn_run = Button(self, text="RUN this configuration", fg="green", width=default_btn_width)
        btn_run['command']= lambda: close_and_call(parent, start_run)
        btn_run_multi = Button(self, text="RUN multiple configurations", fg="green")
        btn_run_multi['command']= lambda: close_and_call(parent, Select_run_multiple_frame)

        lbl1.pack(side=TOP, fill=X)
        lbl2.pack(side=TOP, fill=X)
        mid_frame.pack()
        btn_new_config.pack(side=LEFT)
        btn_edit_config.pack(side=LEFT)
        btn_sel_config.pack(side=LEFT)
        sep1.pack()
        btn_run_multi.pack(side=BOTTOM)
        sep2.pack(side=BOTTOM)
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
        loc = filedialog.asksaveasfilename(title = "Save as", defaultextension='.txt', filetypes = (("text files","*.txt"),("all files","*.*")))
        if conf_name == '' or loc == '' or loc == (): return
        config = Config(conf_name, (loc+".txt"), 0, [])
        global active_config
        active_config = config
        close_and_call(self, lambda: mod_config())

class Mod_config_frame(Frame):
    """
    Frame to modify the currently selected configuration
    """
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
        text = f"Device Name: {dev_conf.name}\nRuntime: {dev_conf.length}s\nBattery test: {dev_conf.is_battery_test}\nIperf Address: {dev_conf.addr}\nTrace: {dev_conf.get_trace_name()}\nCCAs (shows maximal {max_displ}):"
        for cca in dev_conf.ccas:
            count += 1
            if count > max_displ: break
            text += f"\n{cca}"
        self.lbl['text'] = text
    
    def on_modify(self):
        dev_conf = self.get_selected_dev()
        if dev_conf == None: return
        update_dev()
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
    def __init__(self, parent, device:Device, device_config:Dev_config):
        Frame.__init__(self, parent)
        self.dev_conf = device_config #save device to access it from other functions
        self.dev_name = device.name
        self.device = device
        top_lbl = Label(self, text=f"Configuration: \"{active_config.name}\", Device: \"{self.dev_name}\"")
        bot_frame = Frame(self)
        btn_back = Back_btn(bot_frame, cmd=lambda: close_and_call(self,mod_config))
        btn_ok = Ok_btn(bot_frame, self.on_ok)

        #Frame to hold entry boxes to enter the config of the device
        #expose entries with self to functions in class
        lhs = Frame(self)
        length_lbl = Label(lhs, text=f"Enter length of test\n(default in seconds)")
        length_lbl.grid(row=0, column=0)
        self.length_entry = Entry(lhs)
        self.length_entry.grid(row=0, column=1)
        self.length_entry.insert(END, device_config.length)
        self.battery_var = IntVar(value=int(self.dev_conf.is_battery_test))
        checkbtn = Checkbutton(lhs, text="Battery test", variable=self.battery_var)
        checkbtn.grid(row=1)
        trace_txt1 = f"Selected trace file:\n{device_config.get_trace_name()}"
        trace_lbl = Label(lhs, text=trace_txt1)
        trace_lbl.grid(row=2)
        trace_lbl2 = Label(lhs, text=f"Handler: {device_config.trace_handler}")
        trace_lbl2.grid(row=3, column=0)
        trace_select_btn = Button(lhs, text="Select trace", command=self.select_trace)
        trace_select_btn.grid(row=3, column=1)
        ip, port = device_config.addr
        ip_lbl = Label(lhs, text="Enter ip of iperf server")
        ip_lbl.grid(row=4, column=0)
        self.ip_entry = Entry(lhs)
        self.ip_entry.grid(row=4, column=1)
        self.ip_entry.insert(END, ip)
        port_lbl = Label(lhs, text="Enter port of iperf server")
        port_lbl.grid(row=5, column=0)
        self.port_entry = Entry(lhs)
        self.port_entry.grid(row=5, column=1)
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
        Reads all values and checks if they are sensible and result in a correct device configuration, if yes adds it to the configuration
        Returns true if the config was modified, false if an entry was nonvalid
        """
        correct_values = True
        try:
            length_raw = self.length_entry.get().split()
            if len(length_raw) == 1:
                length_factor = 1
            elif len(length_raw) == 2:
                unit = length_raw[1].strip()
                if unit == "s" or unit == "second" or unit == "seconds":
                    length_factor = 1
                elif unit == "min" or unit == "minute" or unit == "minutes":
                    length_factor = 60
                elif unit == "h" or unit == "hour" or unit == "hours":
                    length_factor = 3600
                else:
                    raise ValueError()
            else:
                raise ValueError()
            length = int(length_raw[0]) * length_factor

        except ValueError:
            print("Invalid entry for length, must be a integer strictly larger than 0 with an optional time unit (s, min, h) seperated by whitespace")
            correct_values = False    
        ip = self.ip_entry.get()
        try:
            port = int(self.port_entry.get())
        except ValueError:
            print("Invalid entry for port, must be a single integer")
            correct_values = False
        indices = self.lb.curselection()
        ccas = []
        for i in indices:
            ccas.append(self.lb.get(i))
        
        if correct_values:
            is_battery_test = bool(self.battery_var.get())
            dev_config = Dev_config(self.dev_name, length, is_battery_test, self.dev_conf.trace_name, self.dev_conf.trace_handler, (ip, port), len(ccas), ccas)
            if is_valid_dev_config(dev_config):
                #remove duplicate
                for d in active_config.dev_configs:
                    if d.name == dev_config.name:
                        active_config.dev_configs.remove(d)
                        active_config.num_of_dev -= 1        
                #add dev_conf
                active_config.dev_configs.append(dev_config)
                active_config.num_of_dev += 1
                return True
            else: return False #some entry was invalid
        else: return False #some entry was invalid

    def on_ok(self):
        if self.ok_action():
            close_and_call(self, mod_config)
    
    def select_trace(self):
        if self.ok_action():
            close_and_call(self, lambda:Select_trace_frame(self.dev_conf, self.device))

class Select_trace_frame(Frame):
    def __init__(self, dev_conf:Dev_config, device:Device, debug=False, ret_cmd=None):
        Frame.__init__(self, root, width=window_width, height=window_height)
        self.debug = debug
        self.ret_cmd = ret_cmd #used to specify an alternate return command for debugging
        self.dev_conf = dev_conf
        self.device = device
        self.pack(fill=BOTH)
        top_lbl = Label(self, text=f"Trace selection for device {dev_conf.name}")
        top_lbl.pack(side=TOP)
        trace_txt = f"Selected trace file:\n{dev_conf.trace_name}"
        trace_lbl1 = Label(self, text=trace_txt)
        trace_lbl1.pack(side=TOP)
        trace_select_btn = Button(self, text="Select trace", command=self.select_trace)
        trace_select_btn.pack(side=TOP)
        trace_lbl2 = Label(self, text=f"Select handler:")
        trace_lbl2.pack(side=TOP)
        self.lb = Listbox(self, selectmode=SINGLE)
        self.lb.insert(END, "None")
        for handler in trace_worker.handler_mapping:
            self.lb.insert(END, handler)
        self.lb.pack(side=TOP)
        bot_frame = Frame(self)
        bot_frame.pack(side=BOTTOM)
        ok_btn = Ok_btn(bot_frame, self.ok)
        ok_btn.pack(side=RIGHT)
        back_btn = Back_btn(bot_frame, self.cancel)
        back_btn.pack(side=LEFT)

    def cancel(self):
        if self.debug:
            print("debug")
            close_and_call(self, lambda: self.ret_cmd(self.device, self.dev_conf))
        else:
            close_and_call(self, lambda: mod_dev_config(self.device, self.dev_conf))
    
    def ok(self):
        i = self.lb.curselection()
        if i:
            handler = self.lb.get(i)
            if handler == "None":
                self.dev_conf.trace_name = None
                self.dev_conf.trace_handler = None
            else:
                self.dev_conf.trace_handler = handler
            if self.debug:
                close_and_call(self, lambda: self.ret_cmd(self.device, self.dev_conf))
            else:
                close_and_call(self, lambda: mod_dev_config(self.device, self.dev_conf))
        else: print_error(["No handler was selected"])

    def select_trace(self):
        trace_name = filedialog.askopenfilename(title="Select trace file")
        if trace_name == '' or trace_name == (): return
        self.dev_conf.trace_name = trace_name
        close_and_call(self, lambda: Select_trace_frame(self.dev_conf, self.device, debug=self.debug, ret_cmd=self.ret_cmd))

class Select_run_multiple_frame(Frame):
    """
    Allows to start multiple tests which are run consecutively.
    """
    def __init__(self):
        Frame.__init__(self, root, width=window_width, height=window_height)
        self.pack(fill=BOTH)
        info_txt = f"Number of selected configs: {len(run_state_configs)}"
        info_lbl = Label(self, text=info_txt)
        info_lbl.grid(row=0)
        separator1 = Separator(self)
        separator1.grid(row=1)
        select_btn_txt = "Select config"
        add_lbl_txt = f"To add another config, enter number of runs\nand press \"{select_btn_txt}\""
        add_lbl = Label(self, text=add_lbl_txt)
        add_lbl.grid(row=2)
        self.entry = Entry(self)
        self.entry.grid(row=3, column=0)
        self.entry.insert(END, 0)
        select_btn = Button(self, text=select_btn_txt, command=self.add, width=default_btn_width)
        select_btn.grid(row=3, column=1)
        separator2 = Separator(self, height=40)
        separator2.grid(row=4)
        back_btn = Back_btn(self, self.back)
        back_btn.grid(row=5, column=0)
        run_btn = Button(self, text="RUN", fg="green", command=self.run, width=default_btn_width)
        run_btn.grid(row=5, column=1)

    def add(self):
        conf = load_conf()
        try:
            num_of_runs = int(self.entry.get())
        except ValueError:
            print_error("Invalid number of repetitions")
        if conf:
            for i in range(num_of_runs):
                state = State(conf) #create new state object for each number of run
                run_state_configs.append((state, conf))
            close_and_call(self, Select_run_multiple_frame)
        else:
            print_error("No configuration loaded")

    def back(self):
        clear_run_setup()
        close_and_call(self, home)

    def run(self):
        if len(run_state_configs) <= 0:
            print_error("Cannot run, no configurations selected")
        else:
            close_and_call(self, view_run_progress)
    

class Run_config_frame(Frame):
    def __init__(self, parent):
        """
        Displays information about the current test run.
        """
        Frame.__init__(self, parent, width=window_width, height=window_height)
        self.pack(fill=BOTH)
        self.state, config = run_state_configs[run_number]
        state = self.state
        #Get information about starttime and runtime
        max_time = 0
        for dev_conf in config.dev_configs:
            max_time = max(max_time, dev_conf.length * dev_conf.number_of_cca)
        if max_time > 60:
            time_unit = "minutes"
            max_time = round(max_time/60, 1)
        else:
            time_unit = "seconds"
        if state.started:
            starttime = state.starttime
        else:
            starttime = "Not started"
        run_info = f"Running test {run_number} out of {len(run_state_configs)}\nTest name: {config.name}\nStarttime: {starttime}, minimal runtime: {max_time} {time_unit}"
        lbl_top = Label(self, text=run_info)
        lbl_top.pack(side=TOP)

        lbl_progress = Label(self, text=state.print_status())
        lbl_progress.pack(side=TOP)

        if not state.started:
            run_btn = Button(self, text="RUN", fg="green", command=self.run_conf, width=default_btn_width)
            run_btn.pack()

        if state.pull_complete and not state.all_finished_stage(1):
            lbl = Label(self, text="Not all data was found, see above")
            lbl.pack()
            retry_btn = Button(self, text="RETRY", command=self.retry, width=default_btn_width)
            retry_btn.pack()

        if state.finished:
            ok_btn = Ok_btn(self, self.close_action)
            ok_btn.pack()
        else:
            update_btn = Button(self, text="UPDATE", fg="green", command=self.update, width=default_btn_width)
            update_btn.pack()
            back_btn = Back_btn(self, self.close_action)
            back_btn.pack()
        
    def update(self):
        close_and_call(self, view_run_progress)
    
    def run_conf(self):
        run_conf()
        self.update()

    def close_action(self):
        if (not self.state.started) or self.state.finished:
            clear_run_setup()
            close_and_call(self, home)
        else:
            close_and_call(self, Ask_abort_frame)
    
    def retry(self):
        server.collect_data(self.state)
        self.update()

class Ask_abort_frame(Frame):
    def __init__(self):
        Frame.__init__(self, root, width=window_width, height=window_height)
        self.pack(fill=BOTH)
        lbl = Label(self, text=f"Test has not yet completed.\nAre you sure you want to cancel?")
        lbl.pack(side=TOP)
        bot_frame = Frame(self)
        bot_frame.pack(side=BOTTOM)
        n_btn = Button(bot_frame, text="NO", fg="red", command=self.no, width=default_btn_width)
        n_btn.pack(side=LEFT)
        y_btn = Button(bot_frame, text="YES", fg="green", command=self.yes, width=default_btn_width)
        y_btn.pack(side=RIGHT)

    def no(self):
        close_and_call(self, view_run_progress)
    
    def yes(self):
        clear_run_setup()
        signal_queue.put(3)
        close_and_call(self, home)

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
        conf = Dev_config(dev.name, 0, False, None, None, (server_settings.ip, 0), 0, [])
        mod_dev_config(dev, conf)

def start_run():
    """
    Called when user clicks on 'Run this configuration' on the home window.
    Checks if the configuration is valid and then starts the test run and goes to view_run_progress
    """
    if active_config == None:
        print_error("No configuration selected")
        home()
    else:
        state = State(active_config)
        run_state_configs.append((state, active_config))
        view_run_progress()

def run_conf():
    """
    Runs the configuration at index run_number in the list run_state_configs
    """
    state, config = run_state_configs[run_number]
    if is_valid_config(config):
        if iperf_server.setup():
            iperf_server.start_emulating()
            config_queue.put(config.copy())
            state.start()
        else:
            print_error("Could not setup the iperf server")
    else:
        pass #cannot run invalid configuration

def view_run_progress():
    """
    Show overview of the current run
    """
    Run_config_frame(root)

def clear_run_setup():
    iperf_server.clear_setup()
    run_state_configs.clear()
    global run_number
    run_number = 0
    

def save_conf():
    """
    Writes the current configuration to a file
    """
    f = open(active_config.location, 'w')
    #txt = f"{active_config['name']}, Version 1\nServer_settings:tbd\nNumber_of_devices: {active_config['num_of_dev']}\n"
    txt = f"{active_config.name}, Version 4\nNumber_of_devices: {active_config.num_of_dev}\n"
    for d in active_config.dev_configs:
        txt += dev_conf_to_str(d) + f"\n"
    f.write(txt)

def dev_conf_to_str(dev_conf:Dev_config):
    """
    Writes the device configuration into a string (ends it with newline)
    """
    ip, port = dev_conf.addr
    txt = f"{dev_conf.name},{dev_conf.length},{dev_conf.is_battery_test},{dev_conf.trace_name},{dev_conf.trace_handler},{ip},{port},{dev_conf.number_of_cca}"
    for cca in dev_conf.ccas:
        txt +=f",{cca}"
    return txt

def activate_conf():
    """
    Wrapper function load configuration
    """
    conf = load_conf()
    if conf:
        global active_config
        active_config = conf
    home()
        

def load_conf():
    """
    Asks for a configuration to open, tries to load and return it.
    """
    f_loc = filedialog.askopenfilename(title = "Select configuration file", filetypes = (("text files","*.txt"),("all files","*.*")))
    if f_loc == '' or f_loc == (): return None #no file was selected
    else:
        f = open(f_loc, mode='r')
        line_1 = f.readline().split(',')
        try:
            name, version = line_1[0], int(line_1[1].split()[1]) #reads name & version number of the configuration file
            version_handlers = {
                3: load_v3,
                4: load_v4,
            }
            try: return version_handlers[version](f, name, f_loc) #calls the handler belonging to the version number
            except KeyError: 
                print("Invalid configuration version")
                return None
        except IndexError:
            print("Could not load configuration, reading of name and version failed")
            return None

#load_v* load a specific version

def load_v3(f, name, f_loc):
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
        trace_name = l[2]
        trace_name = to_none(trace_name)
        trace_handler = l[3]
        trace_handler = to_none(trace_handler)
        addr = (l[4], int(l[5]))
        num_cca = int(l[6])
        ccas = []
        for j in range(num_cca):
            ccas.append(l[7+j])
        dev_conf = Dev_config(dev_name, length, False, trace_name, trace_handler, addr, num_cca, ccas)
        dev_list.append(dev_conf)
    return Config(name, f_loc, num_of_dev, dev_list)

def load_v4(f, name, f_loc):
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
        is_battery_test = l[2] == "True"
        trace_name = l[3]
        trace_name = to_none(trace_name)
        trace_handler = l[4]
        trace_handler = to_none(trace_handler)
        addr = (l[5], int(l[6]))
        num_cca = int(l[7])
        ccas = []
        for j in range(num_cca):
            ccas.append(l[8+j])
        dev_conf = Dev_config(dev_name, length, is_battery_test, trace_name, trace_handler, addr, num_cca, ccas)
        dev_list.append(dev_conf)
    return Config(name, f_loc, num_of_dev, dev_list)

def to_none(string:str):
    if string == 'None':
        return None
    else:
        return string


def is_valid_config(config:Config):
    """
    Checks wheter the current configuration is a valid configuration.
    """
    correct_values = True #Set to false if any value does not meet criterea
    error_txt = [f"Invalid configuration \"{config.name}\""]
    if config.name == "":
        correct_values = False
        error_txt.append(f"Invalid configuration name")
    num_dev = len(config.dev_configs)
    if num_dev != config.num_of_dev:
        correct_values = False
        error_txt.append("Length of dev_configs list and num_of_dev don't correspond (Internal error)")
    if num_dev <= 0:
        correct_values = False
        error_txt.append("No device in this test")
    for d in config.dev_configs:
        correct_values = is_valid_dev_config(d) and correct_values
    
    #check if device is connected and has all specified CCAs
    update_dev()
    for dev_conf in config.dev_configs:
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

    if (not correct_values):
        print_error(error_txt)
    return correct_values

def is_valid_dev_config(dev_config:Dev_config):
    """
    Checks wheter a given device configuration is a valid device configuration.
    """
    correct_values = True #Set to false if any value does not meet criterea
    error_txt = [f"Invalid device configuration for {dev_config.name}"]
    if dev_config.length <= 0:
        error_txt.append(f"Invalid length, must be strictly larger than 0, is {dev_config.length}")
        correct_values = False
    correct_values = is_valid_addr(dev_config.addr) and correct_values
    num_cca = len(dev_config.ccas)
    if num_cca != dev_config.number_of_cca:
        correct_values = False
        error_txt.append("Number of selected CCAs is not the same as specified number")
    if num_cca <= 0:
        correct_values = False
        error_txt.append(f"Number of selected CCAs: {num_cca}, must be strictly larger than 0")
    
    if (not correct_values):
        print_error(error_txt)
    return correct_values

def is_valid_addr(addr:tuple):
    """
    Checks wheter a given addr is a valid address.
    """
    valid = True
    ip, port = addr
    try:
        socket.inet_aton(ip)
    except OSError:
        valid = False
        print_error("Given ip address is not valid")
    max_port = 65535
    if not (port >= 0 and port < max_port):
        valid = False
        print_error(f"Port range is invalid, must be between 0 (inclusive) and {max_port}")
    return valid
        
##################################### main function####################################################################################################################################################
def init_tk():
    global root
    root = Tk()
    root.geometry("500x500")
    root.title("Control server")
    root.protocol("WM_DELETE_WINDOW", shutdown) #closing the window also triggers a shutdown of the server


def main(conf_queue:queue.Queue, dvice_queue:queue.Queue, signl_queue:queue.Queue):
    global config_queue, device_queue, signal_queue
    config_queue = conf_queue
    device_queue = dvice_queue
    signal_queue = signl_queue
    init_tk()
    trace_worker.init()
    load_settings()
    home()
    mainloop()

if __name__ == "__main__":
    main(None, None, None) #starts the frontend only, used for debugging