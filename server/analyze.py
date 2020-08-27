import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys

results_folder = "Test_result_experiments"
all_traces = ["bus", "car1", "car2", "ferry", "metro", "train1", "train2", "tram1", "tram2", "tram3"]
all_delays = [5, 25, 100]
all_losses = [0, 1]

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




def plot_throughput_delay_scatter():
    params = get_tests()
    columns = ["test_name", "avg_rtt", "avg_throughput", "artificial loss in %", "cca", "trace", "artificial delay"]
    accumulator = []
    for param in params:
        data = pd.read_csv(param.file_name)
        means = data.mean()
        for cca in ["reno", "cubic"]:
            avg_rtt = means.loc[get_column_name(param.test_name, cca, "rtt")]
            avg_tp = means.loc[get_column_name(param.test_name, cca, "throughput")]
            accumulator.append([param.test_name, avg_rtt, avg_tp, param.loss, cca, param.trace, param.delay])
    
    df = pd.DataFrame(np.array(accumulator), columns=columns)
    df.avg_rtt = df.avg_rtt.astype(float)
    df.avg_throughput = df.avg_throughput.astype(float)
    sns.relplot(x="avg_rtt", y="avg_throughput", data=df, hue="cca", style="artificial loss in %")
    plt.show()


def plot_throughput_delay_line():
    params = get_tests(traces=["bus"], losses=[0], delays=[5])
    accumulator = []
    columns = ["timestamp", "rtt", "throughput", "cca"]
    for param in params:
        data = pd.read_csv(param.file_name)
        for cca in ["reno", "cubic"]:
            rtt = get_column_name(param.test_name, cca, "rtt")
            ts = get_column_name(param.test_name, cca, "timestamp")
            tp = get_column_name(param.test_name, cca, "throughput")
            col = data[rtt]
            data[rtt] = col.map(lambda x: round(x, -1))
            for _, row in data.iterrows():
                #if int(row[rtt]) > 0: #rtt == 0 indicates filler row due to lack of data
                accumulator.append([row[ts], row[rtt], row[tp], cca])

    df = pd.DataFrame(np.array(accumulator), columns=columns)
    df.rtt = df.rtt.astype(float)
    df.timestamp = df.timestamp.astype(float)
    df.throughput = df.throughput.astype(float)

    sns.lineplot(x="rtt", y="throughput", data=df, hue="cca")
    #sns.lineplot(x="timestamp", y="rtt", data=df, hue="cca")
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