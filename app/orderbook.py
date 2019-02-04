import time

from app.utils import give_base_quote
from app.exceptions import OrderBookError


class LimitOrderBook(object):
    """
    very simplistic L.O.B implementation

    It isn't complicated, you can only update the orderbook and
    retrieve information about the best price with get_price.

    There was no need for a more complex implementation for this
    strategy.

    Should probably implement last update ID checking..
    The last_update property is used to check freshness.
    """
    def __init__(self, market):
        self.market = market
        self.base, self.quote = give_base_quote(market)
        self._ask = {}
        self.last_update = None

    def update_level(self, price, quantity):
        self.last_update = time.time()
        if quantity == 0:
            try:
                self._ask.pop(price)
            except KeyError:
                # Receiving an event that removes a price level that is not in
                # your local order book can happen and is normal.
                # https://github.com/binance-exchange/binance-official-api-docs/blob/master/web-socket-streams.md
                pass
            return

        if quantity != 0:
            self._ask[float(price)] = float(quantity)

    def update_levels_from_partial(self, partial):
        """
        accepts a dictionary with key 'asks', a list of price, quantity
        pairs.
        """
        self._ask = {}
        self.last_update = time.time()
        for a in partial["asks"]:
            if float(a[1]) == 0.0 and float(a[0]) in self._ask:
                self._ask.pop(float(a[0]))
                continue
            if float(a[1]) != 0:
                self._ask[float(a[0])] = float(a[1])

            self.last_update = time.time()

    @property
    def best_price(self):
        try:
            b = sorted(self._ask)[0]
        except IndexError as e:
            if len(self._ask.keys()) != 0:
                raise OrderBookError("_ask is not empty but got IndexError on 0.")
            return {"price": 0.0, "quantity": 0}

        return {"price": b, "quantity": self._ask[b]}


# lob = LimitOrderBook("XRPUSDT")
# p = {'timestamp': 1529967373203, 'bid': [['0.03210000', '13.44000000', []], ['0.03205000', '211.79000000', []]],
#     'ask': [['0.03226000', '52.44000000', []], ['0.03226300', '28.72000000', []], ['0.03226400', '12.86000000', []], ['0.03228000', '1.26000000', []]], 'symbol': 'BNBETH', 'original': {'e': 'depthUpdate', 'E': 1529967373203, 's': 'BNBETH', 'U': 54696336, 'u': 54696341, 'b': [['0.03210000', '13.44000000', []], ['0.03205000', '211.79000000', []]], 'a': [['0.03226000', '52.44000000', []], ['0.03226300', '28.72000000', []], ['0.03226400', '12.86000000', []], ['0.03228000', '1.26000000', []]]}, 'exchange': 'binance', 'market': 'BNBETH'}
#
# lob.update_levels_from_partial(p)
# print(lob._ask)
# lob.update_levels_from_partial({"ask": [[0.03226000, 0.0]]})
# print(lob._ask)
# lob.update_levels_from_partial({"ask": [[0.032264, 0]]})
# print(lob._ask)
# print(lob.best_price)
