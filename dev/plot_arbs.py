import json
# import matplotlib.pyplot as plt
import time
import datetime

from asciichart import plot

def tstamp(t):
    return datetime.datetime.fromtimestamp(t).strftime('%H:%M:%S.%f')

with open("arbs.json", "r") as f:
    arbs = json.load(f)

print(arbs.keys())

for path in arbs["path"]:
    print(path)

i = 0
for k, series in arbs["history"].items():
    print("Some timeseries")
    t = [tstamp(float(a["time"])) for a in series]
    z = [t[0], t[-1]]
    v = [float(a["value"]) * 1000 - 1000 for a in series]
    print(len(v))
    if max(v) < 2:
        continue
    print(plot(v))
    input()

    plt.ioff()
    plt.title(k)
    plt.plot(v)
    plt.ylabel('Profit per $1,000')
    plt.xlabel("{} to {}".format(z[0], z[1]))
    plt.savefig('charts/{}.png'.format(k), dpi=plt.gcf().dpi)
    plt.close()
