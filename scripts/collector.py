"""
Used to dump data from ZMQ publisher for later use in profiling, debugging,
etc
"""
import zmq
from config import CONFIG
import json

ctx = zmq.Context()
socket = ctx.socket(zmq.SUB)
socket.connect(CONFIG.ZMQ_SOCKET)
socket.setsockopt(zmq.SUBSCRIBE, CONFIG.ZMQ_TOPIC)
socket.linger = 10

DATA_LENGTH = 100000

data = []
counter = 0

print("Gathering {} lines".format(DATA_LENGTH))
while counter < DATA_LENGTH:
    raw = socket.recv_multipart()

    if not raw:
        continue

    raw[0] = raw[0].decode()
    raw[1] = raw[1].decode()
    data.append(raw)
    counter += 1

    if counter % 100 == 0:
        print("Gathered {}".format(counter))



fd = open("data.raw", mode="w")
fd.write(json.dumps(data))
fd.close()
