# lob = LimitOrderBook("XRPUSDT")

# lob.update_levels_from_partial(p)
# print(lob._ask)
# lob.update_levels_from_partial({"ask": [[0.03226000, 0.0]]})
# print(lob._ask)
# lob.update_levels_from_partial({"ask": [[0.032264, 0]]})
# print(lob._ask)
# print(lob.best_price)
import json
import unittest
import collections

from app import orderbook

with open("app/test/data/graph.json", "r") as f:
    graph = json.load(f)
with open("app/test/data/rates.json", "r") as f:
    rates = json.load(f)
with open("app/test/data/markets.json", "r") as f:
    market_info = json.load(f)
with open("app/test/data/trades.json", "r") as f:
    trade_example = json.load(f)


class TestLimitOrderBook(unittest.TestCase):
    DATA = {
        "timestamp": 1529967373203,
        "bids": [["0.03210000", "13.44000000", []], ["0.03205000", "211.79000000", []]],
        "asks": [
            ["0.03226000", "52.44000000", []],
            ["0.03226300", "28.72000000", []],
            ["0.03226400", "12.86000000", []],
            ["0.03228000", "1.26000000", []],
        ],
        "symbol": "BNBETH",
        "exchange": "binance",
        "market": "BNBETH",
    }

    def test_no_quantity_price_points_removed(self):
        """
        test that when an update with price: 100.00 and quantity: 0.0 is sent
        the key 100.00 is deleted.
        """
        lob = orderbook.LimitOrderBook("XRPUSDT")
        lob.update_levels_from_partial(TestLimitOrderBook.DATA)
        # check the best price is as expected
        self.assertEqual(lob.best_price["price"], 0.03226000)

        # somebody bought all the quantity at the 0.03226000 price point!
        lob.update_level(price=0.03226000, quantity=0)
        # check the price is the next lowest
        self.assertEqual(lob.best_price["price"], 0.03226300)

    def test_remove_none_existant_price_point(self):
        lob = orderbook.LimitOrderBook("XRPUSDT")
        lob.update_levels_from_partial(TestLimitOrderBook.DATA)

        lob.update_level(0.5, 0.0)
        self.assertEqual(lob.best_price["price"], 0.03226000)

    def test_best_price(self):
        pass

    def test_update_level(self):
        pass

    def test_update_level_from_partial_a(self):
        pass

    def test_update_level_from_partial_b(self):
        pass
