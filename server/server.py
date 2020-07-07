import socket
import select
import threading
import time
import queue

import server_frontend
from data_structures import Device, Config, Dev_config

HOST = ''#'127.0.0.1' 
PORT = 65432        # Port to listen on (non-privileged ports are > 1023)

socket_list = [] #list with all active sockets
write_list = [] #list with sockets to be written to
devices = []
shutdown_flag = False

#Queues for communicating between threads
#queue for getting messages to send to devices
config_queue = queue.Queue()
#queue to notify frontend of available devices. This queue is empty unless frontend sends signal 2 (in the signal_queue).
device_queue = queue.Queue()
#different signals: 1=shutdown, 2=update available devices
signal_queue = queue.Queue()


def start_UI():
    """
    Creates and starts a new thread responsible of interaction with the user
    """
    frontend_thread = threading.Thread(target=server_frontend.main, args=(config_queue, device_queue, signal_queue))
    frontend_thread.start()
    return frontend_thread

def server_loop():
    #setup the server
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.setblocking(False)
    server_socket.listen()
    socket_list.append(server_socket)
    print("Server ready")
    terminate = False

    while(not terminate):
        ready_to_read, ready_to_write, in_error = select.select(socket_list, write_list, socket_list, .5)
        #print(f"ready_to_write: {ready_to_write}")
        #Read messages from devices
        for s in ready_to_read:
            if (s == server_socket):
                #new client connected
                client, addr = s.accept()
                socket_list.append(client)
                
                device = Device(client, addr)
                devices.append(device)
            else:
                #potentially reads multiple messages, in practice only one message arrives in read intervall
                data = s.recv(4096)
                device = find_device_by_socket(s)
                handle_msg(data, device)
                
        #Send messages to devices
        for s in ready_to_write:
            if (s == server_socket):
                raise RuntimeError("Cannot write to server_socket")
            else:
                device = find_device_by_socket(s)
                msg = device.write_buff[0]
                device.write_buff.remove(msg)
                msg = bytes(msg, encoding='utf-8')
                s.sendall(msg)
                if not device.write_buff:
                    #remove the device from the write_list if no more message is waiting to be sent
                    write_list.remove(s)

                #close connection if all messages have been sent
                if device.close_flag and (not device.write_buff):
                    remove_device(device)

        #TODO loop over in_error

        update()

        #if the shutdown flag is set and all messages have ben sent, end the loop
        if shutdown_flag and (not write_list):
            terminate = True

def update():
    """
    Polls the queues to get updates from frontend thread
    """
    try:
        i = signal_queue.get_nowait()
        if i == 1:
            shutdown()
        else:
            #i == 2 #update available devices
            device_queue.put(devices.copy())
    except queue.Empty: pass #no signal received, can continue

    try:
        conf = config_queue.get_nowait()
        run_conf(conf)
    except queue.Empty: pass

def shutdown():
    """
    Messages all devices that the connection is terminated and sets the shutdown_flag
    """
    print("Server is shutting down")
    global shutdown_flag
    shutdown_flag = True
    for d in devices:
        send_msg(f",04,Server shutting down\n", d)
        d.close_flag=True

def run_conf(conf:Config):
    name = conf.name
    print(f"Running test {name}\n")
    for dev_conf in conf.dev_configs:
        d = server_frontend.get_dev_by_name(devices, dev_conf.name)
        conf_to_send = dev_conf_to_str(dev_conf)
        msg = f",20,{name},{conf_to_send}\n"
        send_msg(msg, d)

def dev_conf_to_str(dev_conf:Dev_config):
    """
    Writes the device configuration into a string (ends it with newline), ignores traces & name of the device
    """
    ip, port = dev_conf.addr
    txt = f"{dev_conf.length},{ip},{port},{dev_conf.number_of_cca}"
    for cca in dev_conf.ccas:
        txt +=f",{cca}"
    return txt

def find_device_by_socket(s):  
    """
    Finds the device belonging to the socket s
    """
    for d in devices:
        if d.socket == s:
            return d
    raise RuntimeError("Tried to find Invalid socket")

def find_device_by_name(name):
    """
    Finds the device belonging to the name
    """
    for d in devices:
        if d.name == name:
            return d
    raise RuntimeError(f"Could not find device with name {name}")

def remove_device(device:Device):
    """
    Removes device from all queues and closes the corresponding socket
    """
    try: devices.remove(device)
    except ValueError: print(f"Cannot remove {device.name}, device not in device list")
    s = device.socket
    try: write_list.remove(s)
    except ValueError: pass
    try: socket_list.remove(s)
    except ValueError: pass
    s.close()

def handle_msg(raw_data, device:Device):
    """
    Reads a received messages. It first splits the msg into a list of strings, reads which type of msg it is
    and then calls the function handling this type. To view the different types of messages, see structures.txt
    """
    if not raw_data:
        #device has closed the connection
        remove_device(device)
        return
    data = raw_data.decode('utf-8').split(',') #formats the data into a list of strings
    try: msg_type, msg_data = int(data[1]), data[2:]
    except ValueError: print(f"Invalid message received: {data}"); return
    types = {
        1: handle_msg01,
        3: handle_msg03,
        10: handle_msg10,
        21: handle_msg21,
    }
    try:
        types[msg_type](msg_data, device)
    except KeyError:
        print(f"Invalid msg_type {msg_type}")
    
def handle_msg01(msg_data, device:Device):
    print(f"{device.name} writes")
    for str in msg_data:
        print(str)
    print()
    send_msg(f",02,ack 01\n", device)

def handle_msg03(msg_data, device:Device):
    send_msg(f",04,Device requested closing\n", device)
    device.close_flag=True

def handle_msg10(msg_data, device:Device):
    name, ccas = msg_data[0], msg_data[1:]
    device.name = name
    device.ccas = ccas
    send_msg(f",11,ack 01\n", device)

def handle_msg21(msg_data, device):
    print(f"{device.name} returned from a test run with:\n{msg_data}")

def send_msg(msg, device):
    """
    send a message by adding it to the write_buff & adding the socket to the write_list
    """
    device.write_buff.append(msg)
    if write_list.count(device.socket) == 0:
        write_list.append(device.socket)
    else: pass #this socket is already in the write_list, don't add it again

def main():
    
    frontend_thread = start_UI()
    server_loop()
    frontend_thread.join()

if __name__ == "__main__":
    main()