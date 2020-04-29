import time
import queue
from tkinter import *

import server

#Queues for inter thread communication
send_queue:queue.Queue
device_queue:queue.Queue
signal_queue:queue.Queue

#global variables
root:Tk
selected_config = ""
devices = []
window_width = 500
window_height = 500
index=-1

class Separator(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent, height=30)

class Back_to_home_btn(Button):
    def __init__(self, parent):
        Button.__init__(self, parent, text="BACK to HOME", fg="red")
        self["command"]=lambda: close_and_call(parent, home)

class Config_frame(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent, width=window_width, height=200)
        lbl1 = Label(self, text="selected configuration")
        if selected_config == "": display_config = "None"
        else: display_config = selected_config
        lbl2 = Label(self, text=display_config)
        btn_new_config = Button(self, text="Create new", width=10)
        btn_new_config['command']= lambda: close_and_call(parent, lambda:hi_foo("TODO implement creating new config"))
        #TODO add button to edit current selected config
        btn_sel_config = Button(self, text="Select config", width=10)
        btn_sel_config['command']= lambda: close_and_call(parent, lambda:hi_foo("TODO implement select config"))
        lbl1.pack(side=TOP, fill=X)
        lbl2.pack(side=TOP, fill=X)
        btn_new_config.pack(side=LEFT)
        btn_sel_config.pack(side=RIGHT)

"""
Lists all devices and one can select one device, which is then passed to the function
on_select as an argument
"""
class Device_selection(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent)
        self.parent = parent
        self.lb = Listbox(self, selectmode=SINGLE)
        self.lb.pack()
        for d in devices:
            self.lb.insert(END, d["name"])
        self.lb.bind('<<ListboxSelect>>', self.on_dev_select)
    
    def on_dev_select(self, evt):
        w = evt.widget
        try:
            global index
            index = w.curselection()[0]
            close_and_call(self.parent, view_dev)
        except IndexError: pass #if nothing is selected w.curselection()[0] fails

class Devices_frame(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent, width=window_width, height=window_height)
        btn_back = Back_to_home_btn(self)
        btn_update = Button(self, text="UPDATE available devices", fg="blue")
        btn_update["command"] = lambda: close_and_call(self, lambda:call2(update_dev, view_dev))
        select = Device_selection(self)
        if index == -1:
            lbl = Label(self, text="Select a device to see information")
        else:
            dev = devices[index]
            lbl = Label(self, text=f"Name: {dev['name']}\nAddress: {dev['addr']}\nAvailable CCA: {dev['CCA']}")

        btn_update.pack(side=TOP)
        btn_back.pack(side=BOTTOM)
        select.pack(side=LEFT)
        lbl.pack(side=RIGHT)

"""
The main window
"""
class Home(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent, width=window_width, height=window_height)
        self.pack(fill=BOTH)
        sep1 = Separator(self)
        
        btn_view_dev = Button(self, text="See connected devices", fg="blue", height=2)
        btn_view_dev['command'] = lambda: close_and_call(self, view_dev)

        config_frame = Config_frame(self)

        button_quit = Button(self, text="QUIT", bg="red", height=2)
        button_quit['command'] = lambda: shutdown(signal_queue)

        btn_view_dev.pack(side=TOP, fill=X)
        config_frame.pack(side=TOP)
        sep1.pack()
        button_quit.pack(side=BOTTOM, fill=X)

"""
Creates the main window
"""
def home():
    Home(root)

"""
Shows available devices, full information for the device pass as argument dev
"""
def view_dev():
    frame = Devices_frame(root)
    frame.pack(fill=BOTH)
    #TODO show devices


"""
updates the devices list
"""
def update_dev():
    signal_queue.put(2)
    #time.sleep(2)
    try: dev = device_queue.get(timeout=3) #wait for server to fill queue
    except queue.Empty: print("Error: Unable to update devices")
    global devices, index
    index = -1
    devices = dev

"""
This function creates a placeholder window with the str argument as text.
str: string
"""
def hi_foo(str):
    frame = Frame(root)
    frame.pack(fill=BOTH)

    lbl = Label(frame, text=str)
    lbl.pack(side=TOP)

    btn = Back_to_home_btn(frame)
    btn.pack()


"""
Function that destroys the argument to_close & calls 2nd argument foo()
"""
def close_and_call(to_close, foo):
    to_close.destroy()
    foo()

def shutdown(signal_queue):
    signal_queue.put(1)
    quit()

"""
Calls both functions f1 & f2
"""
def call2(f1, f2):
    f1()
    f2()

def main(snd_queue:queue.Queue, dvice_queue:queue.Queue, signl_queue:queue.Queue):
    global send_queue, device_queue, signal_queue, root
    root = Tk()
    root.geometry("500x500")
    root.title("Control server")
    send_queue = snd_queue
    device_queue = dvice_queue
    signal_queue = signl_queue
    home()
    mainloop()

if __name__ == "__main__":
    main(None, None, None)