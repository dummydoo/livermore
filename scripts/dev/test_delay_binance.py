import time
import datetime
import math

from app.cfxws.exchange import Binance

delay = []

QUICK_TEST = 10
REAL_TEST = 300

NO_TESTS = QUICK_TEST


def f(self, msg):
    if self.i <= NO_TESTS:
        delta = datetime.datetime.now() - msg["datetime"]
        delay.append(float(delta.total_seconds()) * 1000)
        self.i = self.i + 1
        print(self.i)
        print(msg)
        return

    print(delay)
    print("avg delay in ms: ", math.fsum(delay) / len(delay))
    print("min delay in ms: ", min(delay))
    print("max delay in ms: ", max(delay))
    quit()


b = Binance()
b.listen_trades(f, ["btcusdt"])
