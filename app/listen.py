"""
The real system used a more complex listener application which attempted
to do some pretty funky things. This is a very basic implementation based
upon my own CFXWS.. which needs a massive rewrite. We could have used the binance lib, but that requires
keys even for unauthenticated websocket channels and endpoints.. effort.
"""
import sys
import signal
import multiprocessing
import time
import json
import zmq


def listen_orderbook(markets):
    """
        Listens for market depth updates and pushes via ZMQ.
        Basic implementation to facilitate public release.

        31/01/2019 - CD

        :param markets list: list of markets
    """
    # Solves multiprocess and twisted issue. See: https://stackoverflow.com/questions/11272874/is-twisted-incompatible-with-multiprocessing-events-and-queues/11283425#11283425
    from twisted.internet import reactor
    from app.cfxws.exchange import Binance

    markets = [m.lower() for m in markets]

    print("LISTEN PROCESS STARTED.")

    ctx = zmq.Context()
    s = ctx.socket(zmq.PUB)
    s.bind(b"tcp://127.0.0.1:5678")

    def push_update(self, msg):
        topic = msg["stream"].split("@")[0].upper()
        s.send_multipart([topic.encode("utf-8"), json.dumps(msg["data"]).encode("utf-8")])

    b = Binance()
    b.listen_depth(push_update, markets)
