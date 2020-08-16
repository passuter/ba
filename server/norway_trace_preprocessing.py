from tkinter import filedialog
from random import randrange
import sys

"""
This file preprocesses the norway traces as specified for the bachelor thesis
i.e. selects random 2min interval and adds (hardcoded) delay & loss 
"""

dst_folder = "loss_traces"

def select_2min(lines):
    num_lines = len(lines)
    #get possible start indices of interval
    end_time = int(lines[num_lines-1].split()[1])
    length = 2 * 60 * 1000 #interval length in ms
    latest_start_time = end_time - length
    latest_start_index = num_lines - 2
    while(True):
        if latest_start_index < 0:
            raise ValueError("No interval exists")
        timestamp = int(lines[latest_start_index].split()[1])
        if timestamp < latest_start_time:
            break
        latest_start_index -= 1

    start_index = randrange(latest_start_index)
    timestamp = int(lines[start_index].split()[1])
    end_time = timestamp + length
    i = start_index + 1
    res = ""
    while timestamp < end_time:
        tokens = lines[i].split()
        interval_length = int(tokens[5])
        num_bytes = int(tokens[4])
        throughput = int(num_bytes/interval_length * 8)
        res += f"{interval_length} {throughput}kbps,"
        i += 1
        timestamp = int(tokens[1])
    return res

def main():
    args = sys.argv
    dst_name = ""
    for i in range(len(args)):
        if args[i] == "-n" or args[i] == "-name":
            try:
                dst_name = args[i+1]
            except IndexError:
                dst_name = ""
    #Get file
    if dst_name == "":
        f = None
        while f==None:
            f = filedialog.askopenfile()
    else:
        f = open(f"norway_traces/{dst_name}.txt", mode='r')

    #process trace
    res_txt = select_2min(f.readlines())

    #save result
    if dst_name == "":
        dst_name = input(f"Enter name of file to save trace\n")
    dst = dst_folder + "/" + dst_name

    for i in range(6):
        dl, dl_name = get_delay_loss(i)
        name = f"{dst}_{dl_name}.txt"
        out = open(name, mode='w')
        out.write(dl + res_txt)
        out.close()

def get_delay_loss(i:int):
    dl = {
        0: f"5\n0\n",
        1: f"25\n0\n",
        2: f"100\n0\n",
        3: f"5\n1\n",
        4: f"25\n1\n",
        5: f"100\n1\n",
    }
    dl_name = {
        0: f"d5l0",
        1: f"d25l0",
        2: f"d100l0",
        3: f"d5l1",
        4: f"d25l1",
        5: f"d100l1",
    }
    return dl[i], dl_name[i]

if __name__ == "__main__":
    main()