import sys
import time

import zmq
import numpy

import collections
import multiprocessing
import json

from autobahn.twisted.websocket import WebSocketClientProtocol
from autobahn.twisted.websocket import WebSocketClientFactory
from autobahn.twisted.websocket import connectWS
from app.cfxws.client import WSClient
from twisted.python import log
from twisted.internet import reactor, ssl


def listen(pid, q):
    print("{} STARTING".format(pid))
    # Import in method.. fix side effect of tornado
    from app.cfxws.exchange import Binance

    def act(_, msg):
        q.put(str(msg))

    def handle_response(_, response, type):
        return response

    factory = WebSocketClientFactory("wss://stream.binance.com:9443/ws/btcusdt@depth5")

    MyWs = WSClient
    MyWs._handle_response = handle_response
    MyWs.handle_method = act
    factory.protocol = MyWs
    contextFactory = ssl.ClientContextFactory()
    connectWS(factory, contextFactory)
    reactor.run()


def main():
    py_msg_queue = multiprocessing.Queue()
    thread = multiprocessing.Process(target=listen, args=(1, py_msg_queue))
    thread.start()

    connect_to = "tcp://127.0.0.1:5678"
    topics = ""

    ctx = zmq.Context()
    s = ctx.socket(zmq.SUB)
    s.setsockopt(zmq.SUBSCRIBE, "")
    s.connect(connect_to)

    messages = collections.defaultdict(dict)
    i = 0

    # check our pyws client is ready!
    for x in range(100):
        time.sleep(0.3)
        try:
            wspy_msg = py_msg_queue.get(block=False)
        except Exception as E:
            wspy_msg = None
        if wspy_msg is not None:
            print("wspy is ready!")
            print(wspy_msg)
            break
        print(x)

    START_TIME = time.time()
    while True:
        if time.time() - START_TIME > 30:
            break

        try:
            _, zmq_msg = s.recv_multipart(flags=zmq.NOBLOCK)
        except Exception as e:
            zmq_msg = None

        try:
            wspy_msg = py_msg_queue.get(block=False)
        except Exception:
            wspy_msg = None

        if wspy_msg:
            wspy_msg = str(wspy_msg)
        if zmq_msg:
            zmq_msg = str(zmq_msg)

        # if zmq_msg:
        #     print("zmq: ", zmq_msg, hash(zmq_msg))
        # if wspy_msg:
        #     print("wspy: ", wspy_msg, hash(wspy_msg))

        d = {"zmq": zmq_msg, "wspy": wspy_msg}

        for k, v in d.items():
            if v:
                messages[hash(v)][k] = {"time": time.time(), "m": k}
    return messages


messages = main()
print(json.dumps(messages, indent=4))

score = collections.defaultdict(int)
for _, unique_messages in messages.items():
    lowest_time = float("inf")
    highest_time = 0
    lowest_m = None
    for k, v in unique_messages.items():
        if v["time"] < lowest_time:
            lowest_time = v["time"]
            lowest_m = v["m"]
        if v["time"] > highest_time:
            highest_time = v["time"]
        score[lowest_m] = score[lowest_m] + 1
        print("{} won by {}".format(lowest_m, highest_time - lowest_time))
