import socket
import select
import threading
import time
import queue

import server_frontend

HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
PORT = 65432        # Port to listen on (non-privileged ports are > 1023)

socket_list = [] #list with all active sockets
write_list = [] #list with sockets to be written to
devices = []
shutdown_flag = False

#Queues for communicating between threads
#queue for getting messages to send to devices
send_queue = queue.Queue()
#queue to notify frontend of available devices
device_queue = queue.Queue()
#different signals: 1=shutdown, 2=update available devices
signal_queue = queue.Queue()


"""
Creates and starts a new thread responsible of interaction with the user
"""
def start_UI():
    #TODO implement start_UI
    frontend_thread = threading.Thread(target=server_frontend.main, args=(send_queue, device_queue, signal_queue))
    frontend_thread.start()

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
        ready_to_read, ready_to_write, in_error = select.select(socket_list, write_list, socket_list, 2)
        #print(f"ready_to_write: {ready_to_write}")
        #Read messages from devices
        for s in ready_to_read:
            if (s == server_socket):
                #new client connected
                client, addr = s.accept()
                socket_list.append(client)
                
                device = {
                    "socket": client,
                    "addr": addr,
                    "name": "Not_initialized",
                    "CCA": [],
                    "write_buff": [],
                    "last_flag": False
                }
                devices.append(device)
            else:
                data = s.recv(4096)
                device = find_device(s)
                handle_msg(data, device)
                
        #Send messages to devices
        for s in ready_to_write:
            if (s == server_socket):
                raise RuntimeError("Cannot write to server_socket")
            else:
                device = find_device(s)
                msg = device["write_buff"][0]
                device["write_buff"].remove(msg)
                msg = bytes(msg, encoding='utf-8')
                s.sendall(msg)
                write_list.remove(s)

                #the sent message is 04, closing the connection. The device can now be removed.
                if device["last_flag"]:
                    remove_device(device)

        #TODO loop over in_error
        update()

        #if the shutdown flag is set and all messages have ben sent, end the loop
        if shutdown_flag and (not write_list):
            terminate = True

"""
Polls the queues to get updates from frontend thread
"""
def update():
    try:
        i = signal_queue.get_nowait()
        if i == 1:
            shutdown()
        else:
            #TODO implement different signal handling
            pass
    except queue.Empty: pass #no signal received, can continue

    #TODO get messages to send from send_queue

"""
Messages all devices that the connection is terminated and sets the shutdown_flag
"""
def shutdown():
    print("Server is shutting down")
    global shutdown_flag
    shutdown_flag = True
    for d in devices:
        send_msg("04,Server shutting down", d)
        d["last_flag"]=True
"""
Finds the device belonging to the socket s
"""
def find_device(s):
    for d in devices:
        if d["socket"] == s:
            return d
    raise RuntimeError("Tried to find Invalid socket")

"""
Removes device from all queues and closes the corresponding socket
"""
def remove_device(device):
    try: devices.remove(device)
    except ValueError: print("Cannot remove {0}, device not in device list".format(device["name"]))
    s = device["socket"]
    try: write_list.remove(s)
    except ValueError: pass
    try: socket_list.remove(s)
    except ValueError: pass
    s.close()

"""
Reads a received messages. It first splits the msg into a list of strings, reads which type of msg it is
and then calls the function handling this type. To view the different types of messages, see msg_types.txt
"""
def handle_msg(data, device):
    if not data:
        remove_device(device)
        return
    data = data.decode('utf-8').split(',') #formatts the data into a list of strings
    try: msg_type, msg_data = int(data[0]), data[1:]
    except ValueError: print("Invalid message received")
    types = {
        1: handle_msg01,
        3: handle_msg03,
        10: handle_msg10
    }
    try:
        types[msg_type](msg_data, device)
    except KeyError:
        print("Invalid msg_type {0}".format(msg_type))
    

def handle_msg01(msg_data, device):
    print("{0} writes".format(device["name"]))
    for str in msg_data:
        print(str)
    print()
    send_msg("02,ack 01", device)

def handle_msg03(msg_data, device):
    send_msg("04,Device requested closing", device)
    device["last_flage"]=True

def handle_msg10(msg_data, device):
    name, ccas = msg_data[0], msg_data[1:]
    device["name"] = name
    device["CCA"] = ccas
    device_queue.put(device)
    send_msg("11,ack 01", device)

"""
send a message by adding the it to the write_buff & adding the socket to the write_list
response: string
"""
def send_msg(response, device):
    device["write_buff"].append(response)
    if write_list.count(device["socket"]) == 0:
        write_list.append(device["socket"])
    else: pass #this socket is already in the write_list, don't add it again

def main():
    
    start_UI()
    server_loop()

if __name__ == "__main__":
    main()