import socket
import select

"""
This mock client is supposed to test the functionalities of the server.
Currently it connects to the server & sends an initialization message, then sends a message to be printed
"""

terminate_self = False #set this flag so that the mock_client terminates after last message sent


HOST = '127.0.0.1'  # The server's hostname or IP address
PORT = 65432        # The port used by the server
send_msg = []
end_flag = True #flag to stop  the server_loop

def handle_msg(data):
    data = data.decode('utf-8').split(',') #formatts the data into a list of strings
    msg_type, msg_data = int(data[0]), data[1:]
    types = {
        2: handle_msg02,
        4: handle_msg04,
        11: handle_msg11,
    }
    try:
        types[msg_type](msg_data)
    except KeyError:
        print(f"Received msg_type {msg_type}, which the mock client cannot handle")

def handle_msg02(msg):
    if terminate_self:
        send_msg.append(bytes("03,", encoding='utf-8'))

def handle_msg04(msg):
    #server closes connection, mock client terminates
    print(f"Connection closed because: {msg[0]}")
    global end_flag
    end_flag = False   

def handle_msg11(msg):
    send_msg.append(bytes("01,Mock client worked", encoding='utf-8'))

def main():
    
    send_msg.append(bytes("10,Bob,CCA_1,CCA_2", encoding='utf-8'))

    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.connect((HOST, PORT))
    while (end_flag):
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