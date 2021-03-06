import socket
import select
from time import sleep

"""
Author: Pascal Suter
This mock client is supposed to test the functionalities of the server.
It can connect to the server and register itself as a device, and receive and respond to a test configuration. It will not generate any data.
"""

terminate_self = False #set this flag so that the mock_client terminates after it sent its messages. On False it will continue to
                        #read until the server shuts down the connection


HOST = '192.168.1.121'#'127.0.0.1'  # The server's hostname or IP address 
PORT = 65432        # The port used by the server
send_msg = []
end_flag = False #flag to stop  the server_loop
name = "Bob"

def handle_msg(data):
    if not data:
        global end_flag
        end_flag = True
    data = data.decode('utf-8').rstrip().split(',') #formatts the data into a list of strings
    msg_type, msg_data = int(data[1]), data[2:]
    types = {
        2: handle_msg02,
        4: handle_msg04,
        11: handle_msg11,
        20: handle_msg20,
    }
    try:
        types[msg_type](msg_data)
    except KeyError:
        print(f"Received msg_type {msg_type}, which the mock client cannot handle")

def handle_msg02(msg):
    if terminate_self:
        send_msg.append(bytes(",03,", encoding='utf-8'))

def handle_msg04(msg):
    #server closes connection, mock client terminates
    print(f"Connection closed because: {msg[0]}")
    global end_flag
    end_flag = True   

def handle_msg11(msg):
    print("Mock client worked")

def handle_msg20(msg):
    """
    msg20 is a configuration. The mock client will print the configuration and respond succesfull after 2 seconds
    """
    conf_name = msg[0]
    length = int(msg[1])
    is_battery = bool(msg[2] == "True")
    addr = (msg[3],int(msg[4]))
    num_cca = int(msg[5])
    ccas = msg[6:6+num_cca]
    print(f"I received configuration {conf_name}")
    print(f"Length: {length}s, Address: {addr}, CCAs: {ccas}\n")
    if is_battery:
        print(f"This is a battery test")
    sleep(2)
    send_msg.append(bytes(f",21,{conf_name}", encoding='utf-8'))

def main():
    
    send_msg.append(bytes(f",10,{name},CCA_1,CCA_2", encoding='utf-8'))

    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.connect((HOST, PORT))
    while (not end_flag):
        ready_to_read, ready_to_write, in_error = select.select([conn], [conn], [conn], 10)
        for s in ready_to_read:
            data = s.recv(4096)
            handle_msg(data)

        for s in ready_to_write:
            for msg in send_msg:
                s.sendall(msg)
                send_msg.remove(msg)

if __name__ == "__main__":
    main()