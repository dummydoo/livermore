"""
Test for performanc regresions between functions as of 10/10/18
and current implementation.
"""

import time
import unittest

from app import utils


class GiveBaseQuotePerformance(unittest.TestCase):
    def test_no_regression(self):
        new_start = time.time()
        for i in range(10000):
            utils.give_base_quote("BTCUSDT")
            utils.give_base_quote("ETHBTC")
        new_end = time.time()
        new_time_taken = new_end - new_start

        vanilla_start = time.time()
        for i in range(10000):
            utils.give_base_quote("BTCUSDT")
            utils.give_base_quote("ETHBTC")
        vanilla_end = time.time()

        vanilla_time_taken = vanilla_end - vanilla_start

        self.assertLess(new_time_taken, vanilla_time_taken)


class GivePairMarketDirection(unittest.TestCase):
    def test_no_regression(self):
        pass


# stupid - something better?


def vanilla_give_base_quote(market):
    """in a pair; decide which is the base and which is the quote"""
    m = market.upper()

    quote_currencies = [
        "BTC",
        "ETH",
        "USDT",
        "BNB",
        "EOS",
        "XRP",
        "USD",
        "GBP",
        "EUR",
        "CHF",
        "GHS",
        "NEO",
    ]

    base = ""
    quote = ""

    for c in quote_currencies:
        l = len(c)
        if m[-l:] == c:
            quote = c
            base = m[:-l]
    return base, quote


def vanilla_give_pair_market_direction(markets, cfrom, cto):
    """ used to decide which direction we need to go to get the desired trade """
    fromto = "".join([cfrom, cto])
    tofrom = "".join([cto, cfrom])

    if fromto in markets:
        market = fromto
    elif tofrom in markets:
        market = tofrom

    base, quote = give_base_quote(market)

    # If going from base to quote you need to sell
    if cfrom == base and cto == quote:
        return market, "SELL"

    # If going from quote to base, you need to buy
    if cfrom == quote and cto == base:
        return market, "BUY"
