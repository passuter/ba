import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys

results_folder = "Test_result_experiments"
all_traces = ["bus", "car1", "car2", "ferry", "metro", "train1", "train2", "tram1", "tram2", "tram3"]
all_delays = [5, 25, 100]
all_losses = [0, 1]
all_ccas = ["reno", "cubic"]

class Parameter:
    trace:str
    delay:int
    loss:int
    num:int
    test_name:str
    file_name:str

    def __init__(self, trace, delay, loss, num=0):
        self.trace = trace
        self.delay = delay
        self.loss = loss
        self.num = num
        self.test_name = f"{self.trace}_d{self.delay}l{self.loss}"
        self.file_name = f"{results_folder}/{self.test_name}_{self.num}/{self.test_name}_combined.csv"

class Btry_parameter:
    type:str
    loss:int
    test_name:str
    folder:str

    def __init__(self, type, loss, num=0):
        self.type = type
        self.loss = loss
        if type == "normal":
            type = ""
        else:
            type = f"_{type}"    
        self.test_name = f"battery_l{loss}{type}"
        self.folder = f"{results_folder}/{self.test_name}_{num}/"

def get_tests(traces=all_traces, delays=all_delays, losses=all_losses):
    res = []
    for trace in traces:
        for delay in delays:
            for loss in losses:
                if loss == 0:
                    res.append(Parameter(trace, delay, loss))
                else:
                    for num in range(3):
                        res.append(Parameter(trace, delay, loss, num))
    return res

def get_battery_tests(types=["normal", "lowband"], losses=all_losses):
    res = []
    for t in types:
        for l in losses:
            if l == 0:
                res.append(Btry_parameter(t, l))
            else:
                for num in range(3):
                    res.append(Btry_parameter(t, l, num))
    return res

def get_column_name(test_name, cca, type="throughput"):
    """
    type must be either throughput, rtt, loss or timestamp
    """
    if type == "throughput":
        ending = "throughput"
    elif type == "rtt":
        ending = "avg_RTT"
    elif type == "loss":
        ending = "loss"
    elif type == "timestamp" or type == "Timestamp":
        ending = "Timestamp"
    else:
        raise ValueError(f"Invalid column type: {type}")
    return f"{test_name}_Redmi4A_{cca}_{ending}"


def plot_max_rtt():
    columns = ["test_name", "reno_max_rtt", "cubic_max_rtt", "params", "artificial loss in %"]
    accumulator = []
    params = get_tests()
    for param in params:
        data = pd.read_csv(param.file_name)
        maximums = data.max()
        reno_max_rtt = maximums.loc[f'{param.test_name}_Redmi4A_reno_avg_RTT']
        cubic_max_rtt = maximums.loc[f'{param.test_name}_Redmi4A_cubic_avg_RTT']
        accumulator.append([param.test_name, reno_max_rtt, cubic_max_rtt, param, param.loss])
    df = pd.DataFrame(np.array(accumulator), columns=columns)
    #print(df)
    sns.relplot(x="cubic_max_rtt", y="reno_max_rtt", data=df, hue="artificial loss in %", style="artificial loss in %")
    plt.show()

def plot_avg_rtt():
    columns = ["test_name", "reno_avg_rtt", "cubic_avg_rtt", "params", "artificial loss in %"]
    accumulator = []
    params = get_tests()
    for param in params:
        data = pd.read_csv(param.file_name)
        maximums = data.mean()
        reno_max_rtt = maximums.loc[f'{param.test_name}_Redmi4A_reno_avg_RTT']
        cubic_max_rtt = maximums.loc[f'{param.test_name}_Redmi4A_cubic_avg_RTT']
        accumulator.append([param.test_name, reno_max_rtt, cubic_max_rtt, param, param.loss])
    df = pd.DataFrame(np.array(accumulator), columns=columns)
    #print(df)
    sns.relplot(x="cubic_avg_rtt", y="reno_avg_rtt", data=df, hue="artificial loss in %", style="artificial loss in %")
    plt.show()  

def compute_avg_tp_limit(trace:str):
    """
    Computes the wheigted average of the bandwith limit for a specific trace
    """
    f = open(f"loss_traces/{trace}_d5l0.txt")
    values = f.readlines()[2].split(',')
    times = []
    tps = []
    for v in values:
        try:
            time = int(v.split()[0])
            tp = int(v.split()[1].split('k')[0]) * time
            times.append(time)
            tps.append(tp)
        except IndexError:
            #raised at last element, which is empty
            pass
    avg_time = np.mean(time)
    avg_tp = np.mean(tps) / avg_time
    return avg_tp #convert from kilobits per second to kilobytes per second
    
def plot_trace(trace:str):
    f = open(f"loss_traces/{trace}_d5l0.txt")
    values = f.readlines()[2].split(',')
    accumulator = []
    columns = ["timestamp", "tp"]
    timestamp = 0
    for v in values:
        try:
            time = int(v.split()[0])
            tp = int(v.split()[1].split('k')[0])
            accumulator.append([timestamp+1, tp])
            timestamp += time
            accumulator.append([timestamp, tp])
        except IndexError:
            pass
    
    df = pd.DataFrame(np.array(accumulator), columns=columns)
    df.timestamp = df.timestamp.astype(float)
    df.tp = df.tp.astype(float)
    sns.lineplot(x="timestamp", y="tp", data=df)
    plt.show()
    

def plot_throughput_delay_scatter():
    all_traces.remove("ferry")
    all_traces.remove("metro")
    all_traces.remove("tram3")
    params = get_tests()
    columns = ["test_name", "avg_rtt", "avg_throughput", "artificial loss in %", "cca", "trace", "artificial delay", "avg_tp_norm", "avg_rtt_norm"]
    accumulator = []
    for param in params:
        data = pd.read_csv(param.file_name)
        means = data.mean()
        avg_throughput_limitation = compute_avg_tp_limit(param.trace)
        for cca in all_ccas:
            avg_rtt = means.loc[get_column_name(param.test_name, cca, "rtt")]
            avg_rtt_normalized = avg_rtt - param.delay
            avg_tp = means.loc[get_column_name(param.test_name, cca, "throughput")]
            avg_tp_normalized = avg_tp/avg_throughput_limitation
            accumulator.append([param.test_name, avg_rtt, avg_tp, param.loss, cca, param.trace, param.delay, avg_tp_normalized, avg_rtt_normalized])
    
    df = pd.DataFrame(np.array(accumulator), columns=columns)
    df.avg_rtt = df.avg_rtt.astype(float)
    df.avg_throughput = df.avg_throughput.astype(float)
    df.avg_rtt_norm = df.avg_rtt_norm.astype(float)
    df.avg_tp_norm = df.avg_tp_norm.astype(float)
    sns.relplot(x="avg_rtt_norm", y="avg_tp_norm", data=df, hue="cca", style="artificial loss in %")
    plt.show()


def plot_throughput_delay_line():
    #params = get_tests(traces=["bus"], losses=[0], delays=[25])
    params = get_tests(traces=["ferry"], losses=[0])
    accumulator = []
    columns = ["timestamp", "rtt", "throughput", "cca", "trace", "artificial delay", "artificial loss", "test_name"]
    for param in params:
        data = pd.read_csv(param.file_name)
        for cca in all_ccas:
            rtt = get_column_name(param.test_name, cca, "rtt")
            ts = get_column_name(param.test_name, cca, "timestamp")
            tp = get_column_name(param.test_name, cca, "throughput")
            col = data[rtt]
            data[rtt] = col.map(lambda x: 5*round(x/5, -1))
            for _, row in data.iterrows():
                filter = int(row[rtt]) > 0 and int(row[rtt]) < 200000
                if True: #rtt == 0 indicates filler row due to lack of data
                    accumulator.append([row[ts], row[rtt], row[tp], cca, param.trace, param.delay, param.loss, f"{param.test_name}_{param.num}"])

    df = pd.DataFrame(np.array(accumulator), columns=columns)
    df.rtt = df.rtt.astype(float)
    df.timestamp = df.timestamp.astype(float)
    df.throughput = df.throughput.astype(float)

    #sns.lineplot(x="rtt", y="throughput", data=df, hue="cca")
    sns.lineplot(x="timestamp", y="throughput", data=df, hue="cca")
    plt.show()

def plot_btry():
    params = get_battery_tests()
    accumulator = []
    columns = ["avg_throughput", "battery_consumption", "type", "loss", "cca"]
    for p in params:
        data_btry = pd.read_csv(f"{p.folder}{p.test_name}_battery_results.csv")
        data_tp = pd.read_csv(f"{p.folder}iperf_res.csv")
        tp_mean = data_tp.mean()
        for cca in all_ccas:
            tp_colum = f"Redmi4A with cca {cca}"
            btry_colum = f"{p.test_name}_Redmi4A_{cca}_battery_pct"
            avg_tp = round(float(tp_mean.loc[tp_colum])/8000, 1) #convert from bits/second to KBps
            btry_consumed = data_btry.max().loc[btry_colum] - data_btry.min().loc[btry_colum]
            accumulator.append([avg_tp, btry_consumed, p.type, p.loss, cca])
    df = pd.DataFrame(np.array(accumulator), columns=columns)
    df.avg_throughput = df.avg_throughput.astype(float)
    df.battery_consumption = df.battery_consumption.astype(float)
    print(df)
    sns.relplot(x="avg_throughput", y="battery_consumption", data=df, hue="cca", style="type")
    plt.show()



if __name__ == "__main__":
    args = sys.argv
    global pram_num
    try:
        param_num = int(args[1])
    except:
        param_num = 0
    plot_throughput_delay_scatter()
    #plot_throughput_delay_line()
    #plot_btry()
    #plot_trace("ferry")