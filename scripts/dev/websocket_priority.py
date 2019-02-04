import time
import collections
import threading
import multiprocessing
from operator import itemgetter
from datetime import datetime

past = []  # past seconds
threads = []
second_by_second = collections.defaultdict(
    list
)  # key second, list of dicts where t is time and pid is pid
winners = []

queues = []


def this_second():
    return int(time.time())


def listen(pid, act, q):
    print("{} STARTING".format(pid))
    # Import in method.. fix side effect of tornado
    from app.cfxws.exchange import Binance

    b = Binance()
    b.listen_trades(act, ["btcusdt"])


wait_time = time.time() + 45


def make_act(id):
    def this_act(_, msg):
        me = id
        if time.time() > wait_time:
            q.put({"s": int(time.time()), "t": time.time(), "pid": me})

    return this_act


for i in range(40):
    q = multiprocessing.Queue()
    t = multiprocessing.Process(target=listen, args=(i, make_act(i), q))
    threads.append(t)
    queues.append(q)

for t in threads:
    t.start()

START_TIME = time.time()


while True:
    time.sleep(0.001)

    this_sec = this_second()
    for q in queues:
        try:
            x = q.get(block=False)
        except Exception as e:
            continue
        if x is not None:
            second_by_second[this_sec].append(x)

    if time.time() - START_TIME + 30 > 120:
        print("FINISHED")
        break

print(second_by_second.keys())

# Sort the messsages for each second. Append the winning process id to the winners list.
for k, records in second_by_second.items():
    if records is None:
        print(k)
        continue

    sorted_records = sorted(records, key=itemgetter("t"))
    w = sorted_records[0]
    winners.append(w["pid"])
    print("WINNER: {} {} | {}".format(w["pid"], w["t"], sorted_records[-1]))

# Count the wins per process id
wins_by_pid = collections.defaultdict(int)
for p in winners:
    wins_by_pid[p] += 1

# sort by wins
wins_by_pid = sorted(wins_by_pid.items(), key=itemgetter(1), reverse=True)
print(wins_by_pid[0])
print(wins_by_pid[-1])

for k, v in wins_by_pid:
    print(k, " | ", v)

for t in threads:
    t.join()
