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
    throughput_limit:int 
    loss:int
    test_name:str
    folder:str

    def __init__(self, type, loss, num=0):
        self.type = type
        self.loss = loss
        if type == "normal":
            type = ""
            self.throughput_limit = 1000
        else:
            type = f"_{type}"
            self.throughput_limit = 50
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
    return avg_tp
    
def plot_trace(trace:str):
    f = open(f"loss_traces/{trace}_d5l0.txt")
    values = f.readlines()[2].split(',')
    accumulator = []
    columns = ["timestamp", "tp"]
    timestamp = 0
    for v in values:
        try:
            time = float(v.split()[0]) / 1000
            tp = int(v.split()[1].split('k')[0])
            accumulator.append([timestamp+1, tp])
            timestamp += time
            accumulator.append([timestamp, tp])
        except IndexError:
            pass
    
    df = pd.DataFrame(np.array(accumulator), columns=columns)
    df.timestamp = df.timestamp.astype(float)
    df.tp = df.tp.astype(float)
    plot = sns.lineplot(x="timestamp", y="tp", data=df)
    #plot.set_title(f"Bandwidth trace \"{trace}\"")
    plot.set_xlabel("Time (seconds)", fontsize=12)
    plot.set_ylabel("Throughput limit (KBps)", fontsize=12)
    plt.show()
    

def plot_throughput_delay_scatter():
    sns.set_style("whitegrid")
    all_traces.remove("ferry")
    all_traces.remove("metro")
    all_traces.remove("tram3")
    params = get_tests(traces=["metro"])
    columns = ["test_name", "avg_rtt", "avg_throughput", "Artificial loss", "CCA", "trace", "Artificial delay", "avg_tp_norm", "avg_rtt_norm"]
    accumulator = []
    mean_tp_accumulator = [[], [], []]
    delay_map = {5: 0, 25: 1, 100: 2}
    for param in params:
        data = pd.read_csv(param.file_name)
        means = data.mean()
        avg_throughput_limitation = compute_avg_tp_limit(param.trace)
        for cca in ["cubic"]:
            avg_rtt = means.loc[get_column_name(param.test_name, cca, "rtt")]
            avg_rtt_normalized = avg_rtt - param.delay
            avg_tp = means.loc[get_column_name(param.test_name, cca, "throughput")]
            avg_tp_normalized = avg_tp/avg_throughput_limitation
            accumulator.append([param.test_name, avg_rtt, avg_tp, str(param.loss)+"%", cca, param.trace, str(param.delay) + "ms", avg_tp_normalized, avg_rtt_normalized])
            mean_tp_accumulator[delay_map[param.delay]].append(avg_tp_normalized)
            
    mean_tp5 = []
    mean_tp25 = []
    mean_tp100 = []
    for rtt in [100, 2900]:
    #for rtt in [1, 78]:
        mean_tp5.append([np.mean(mean_tp_accumulator[0]), rtt])
        mean_tp25.append([np.mean(mean_tp_accumulator[1]), rtt])
        mean_tp100.append([np.mean(mean_tp_accumulator[2]), rtt])

    mean_df5 = pd.DataFrame(mean_tp5, columns=["mean_tp", "rtt"])
    mean_df25 = pd.DataFrame(mean_tp25, columns=["mean_tp", "rtt"])
    mean_df100 = pd.DataFrame(mean_tp100, columns=["mean_tp", "rtt"])

    df = pd.DataFrame(np.array(accumulator), columns=columns)
    df.avg_rtt = df.avg_rtt.astype(float)
    df.avg_throughput = df.avg_throughput.astype(float)
    df.avg_rtt_norm = df.avg_rtt_norm.astype(float)
    df.avg_tp_norm = df.avg_tp_norm.astype(float)
    #sns.lineplot(x="rtt", y="mean_tp", data=mean_df, hue="art_delay")
    plot = sns.relplot(x="avg_rtt_norm", y="avg_tp_norm", data=df, style="Artificial loss", s=100)
    plot.set_xlabels("Average RTT (without artificial delay, in miliseconds)", fontsize=12)
    plot.set_ylabels("Normalized throughput", fontsize=12) #average throughput achieved relative to average throughput limit
    #plt.title("Throughput/delay comparison, \"metro\" trace")
    plot.fig.set_size_inches(4,4)
    #plot.axes[0,0].plot(mean_df100.rtt, mean_df100.mean_tp, "g-", marker="s")
    #plot.axes[0,0].plot(mean_df25.rtt, mean_df25.mean_tp, "g--", marker="x")
    #plot.axes[0,0].plot(mean_df5.rtt, mean_df5.mean_tp, "g:", marker="o")
    #no loss
    #plot.set(xlim=(0,3000))
    #plot.set(ylim=(0.6,1.1))
    #loss
    #plot.set(xlim=(0,80))
    #plot.set(ylim=(0,1))
    #combined
    #plot.set(xlim=(-50, 3000))
    #plot.set(ylim=(0, 1.1))
    #metro
    plot.set(xlim=(0, 17500))
    plot.set(ylim=(0.1, 0.65))
    plt.show()


def plot_throughput_delay_line():
    #params = get_tests(traces=["bus"], losses=[1])
    params = get_tests(traces=["metro"], losses=[1], delays=[5])
    accumulator = []
    columns = ["timestamp", "rtt", "throughput", "cca", "trace", "artificial delay", "artificial loss", "test_name", "throughput_norm", "rtt_norm"]
    for param in params:
        data = pd.read_csv(param.file_name)
        avg_throughput_limitation = compute_avg_tp_limit(param.trace)
        for cca in all_ccas:
            rtt = get_column_name(param.test_name, cca, "rtt")
            ts = get_column_name(param.test_name, cca, "timestamp")
            tp = get_column_name(param.test_name, cca, "throughput")
            col = data[rtt]
            data[rtt] = col.map(lambda x: round(x))
            for _, row in data.iterrows():
                tp_normalized = float(row[tp])/avg_throughput_limitation
                rtt_norm = row[rtt] - param.delay
                filter = int(row[rtt]) > 0 #and rtt_norm < 100 #rtt == 0 indicates filler row due to lack of data
                if filter: 
                    accumulator.append([row[ts], row[rtt], row[tp], cca, param.trace, param.delay, param.loss, f"{param.test_name}_{param.num}", tp_normalized, rtt_norm])

    df = pd.DataFrame(np.array(accumulator), columns=columns)
    df.rtt = df.rtt.astype(float)
    df.timestamp = df.timestamp.astype(float)
    df.throughput = df.throughput.astype(float)
    df.throughput_norm = df.throughput_norm.astype(float)
    df.rtt_norm = df.rtt_norm.astype(float)

    #plot = sns.lineplot(x="rtt_norm", y="throughput", data=df, hue="cca")
    
    plot = sns.lineplot(x="timestamp", y="rtt", data=df, hue="cca")
    #plot.set_title(f"RTT over time for trace metro, without loss")
    plot.set_xlabel("Timestamp (seconds)", fontsize=12)
    plot.set_ylabel("RTT (miliseconds)", fontsize=12)
    
    plt.show()

def plot_btry():
    sns.set_style("whitegrid")
    params = get_battery_tests()
    accumulator = []
    columns = ["avg_throughput", "battery_consumption", "type", "Artificial loss", "cca"]
    for p in params:
        data_btry = pd.read_csv(f"{p.folder}{p.test_name}_battery_results.csv")
        data_tp = pd.read_csv(f"{p.folder}iperf_res.csv")
        tp_mean = data_tp.mean()
        for cca in ["reno"]:
            tp_colum = f"Redmi4A with cca {cca}"
            btry_colum = f"{p.test_name}_Redmi4A_{cca}_battery_pct"
            avg_tp = round(float(tp_mean.loc[tp_colum])/8000, 4) #convert from bits/second to KBps
            btry_consumed = data_btry.max().loc[btry_colum] - data_btry.min().loc[btry_colum]
            accumulator.append([avg_tp, btry_consumed, p.type, str(p.loss) + "%", cca])
    df = pd.DataFrame(np.array(accumulator), columns=columns)
    df.avg_throughput = df.avg_throughput.astype(float)
    df.battery_consumption = df.battery_consumption.astype(float)
    print(df)
    plot = sns.relplot(x="avg_throughput", y="battery_consumption", data=df, style="Artificial loss", s=200)
    plot.set_xlabels("Average throughput (KBps)", fontsize=12)
    plot.set_ylabels("Battery consumption (%)", fontsize=12)
    plot.fig.set_size_inches(4,4)
    plot.set(xlim=(0,1000))
    plot.set(ylim=(1.7, 8.2))
    #plt.title("Battery/throughput comparison for cubic", fontsize=15)
    plt.show()

def distplot():
    sns.set_style("whitegrid")
    #all_traces.remove("ferry")
    all_traces.remove("metro")
    all_traces.remove("tram3")
    params = get_tests()
    acc = {"reno": [], "cubic": []}
    columns = ["rtt"]
    for p in params:
        data = pd.read_csv(p.file_name)
        avg_tp_limit = compute_avg_tp_limit(p.trace)
        for cca in all_ccas:
            #col = get_column_name(p.test_name, cca, "throughput")
            col = get_column_name(p.test_name, cca, "rtt")
            for _, row in data.iterrows():
                #val = row[col]/avg_tp_limit
                val = row[col] - p.delay
                if val > 0:
                    acc[cca].append([val])
    d1 = pd.DataFrame(np.array(acc["reno"]), columns=columns)
    d2 = pd.DataFrame(np.array(acc["cubic"]), columns=columns)
    sns.distplot(d1.rtt, hist=False, color="b", kde_kws={'cumulative': True, 'linestyle':'-'})
    sns.distplot(d2.rtt, hist=False, color="r", kde_kws={'cumulative': True, 'linestyle':'--'})
    #plt.xlabel("Normalized Throughput")
    plt.xlabel("RTT without artificial delay (ms)")
    plt.ylabel("CDF probability")
    #plt.title("CDF normalized RTT without loss, reno (blue, solid line) and cubic (red, dashed line)")
    plt.show()

def find_outlier():
    all_traces.remove("ferry")
    params = get_tests()
    columns = ["tp_norm", "trace", "test_name", "cca"]
    acc = []
    for p in params:
        data = pd.read_csv(p.file_name)
        avg_tp_limit = compute_avg_tp_limit(p.trace)
        for cca in all_ccas:
            col = get_column_name(p.test_name, cca, "throughput")
            for _, row in data.iterrows():
                val = row[col]/avg_tp_limit
                if val > 5:
                    acc.append([val, p.trace, p.test_name, cca])
    df = pd.DataFrame(acc, columns=columns)
    print(df)

if __name__ == "__main__":
    args = sys.argv
    global param_num
    try:
        param_num = int(args[1])
    except:
        param_num = 0
    #plot_throughput_delay_scatter()
    #plot_throughput_delay_line()
    #plot_btry()
    #for trace in all_traces:
    #    plot_trace(trace)
    #plot_trace("metro")
    distplot()
    #find_outlier()