import math
import time
import datetime
import collections
import json
import logging
from builtins import FileNotFoundError
from config import CONFIG
from app import const
from app.exceptions import NoMarketError, QuantityTooSmallError
from binance.client import Client

LOGGER = logging.getLogger(__name__)


class SimpleNwmon(object):
    """
    Monitors API requests to binance and lets the user know
    if more paths can be exectued. Replaces the more complex NetworkMonitor
    class which also monitored network conditions to decide if they were
    conducive to good trading.
    """
    ORDERS_P_S = 10          # Orders per second
    ORDERS_P_D = 100 * 1000  # Orders per day

    def __init__(self):
        self.orders_pd = collections.defaultdict(int)
        self.orders_ps = collections.defaultdict(int)

    def iterate_order(self):
        d = datetime.datetime.today().day
        s = int(time.time())
        self.orders_pd[d] += 1
        self.orders_ps[s] += 1

    def can_complete_path(self, length):
        d = datetime.datetime.today().day
        s = int(time.time())
        sec_ok = bool(self.orders_ps[s] + length <= SimpleNwmon.ORDERS_P_S)
        day_ok = bool(self.orders_pd[d] + length <= SimpleNwmon.ORDERS_P_D)

        return (day_ok and sec_ok)

    def clean(self):
        """call once time sensitive processes are complete"""
        raise NotImplementedError("Implement me!!")


def give_pair_market_direction(markets, cfrom, cto):
    """
    used to decide which direction we need to go to get the desired trade

    :cfrom: Currency you have; eg "BTC"
    :cto: Currency you want; eg "USDT"

    returns the market and trade direction to get what you want or raises
    NoMarketError if it's not possible.

    """
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

    raise NoMarketError(const.NO_MARKET_ERROR.format(base, quote))


def give_base_quote(market):
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


def add_to_graph(gd, rd, base, rate, quote, TRANSACTION_COST):
    rate = float(rate)
    rate = rate * (1.0 - TRANSACTION_COST)
    w = math.log10(rate)
    # Mathematically log10(x) + log10(1/x) = 0

    gd[base][quote] = -w
    gd[quote][base] = w

    rd[base][quote] = rate
    rd[quote][base] = 1 / rate


def give_source_value(currency, amount, rates, source="USDT"):
    """
    Get the value of x of currency in the source (default USDT)
    """
    if source in rates[currency]:
        return amount * rates[currency][source]
    else:
        return amount * (rates[currency]["BTC"] * rates["BTC"][source])


def give_max_quantity_through_path(trades, rates, order_books, current_bal):
    """
    This method must workout the initial maximum balaQuantityTooSmallErrornce
    we can put through a cycle.

    That value is not the quantity in the book for the first trade. It is the
    lowest unit
    of the initial currency which can be put through the book at this time.

    Luckily hash map lookups are O(n)
    """
    max = current_bal
    for trade in trades:
        base, quote = give_base_quote(trade["market"])
        q = give_source_value(
            base, order_books[trade["market"]].best_price["quantity"], rates
        )
        if q < max:
            max = q
    return max


def closest_tradeable_quantity(m_info, quantity):
    """

    m_info = {
        "PRICE_FILTER": {
            "minPrice": "0.00000100",
            "maxPrice": "1000000.00",
            "tickSize": "0.00000100",
        },
        "LOT_SIZE": {
            "minQty": "0.00100000",
            "maxQty": "100000.00000000",
            "stepSize": "0.00100000"
        },
    }


    :param m_info: dict; market info. filters key from get_symbol info
    :param quantity: float
    """
    if quantity >= m_info["LOT_SIZE"]["minQty"]:
        if quantity % m_info["LOT_SIZE"]["stepSize"] == 0:
            return round(quantity, 8)
        else:
            quantity = (
                int(quantity / m_info["LOT_SIZE"]["stepSize"])
                * m_info["LOT_SIZE"]["stepSize"]
            )
            return round(quantity, 8)

    raise QuantityTooSmallError(
        (
            "This quantity is too small to be traded on this ticker."
            " quantity | min, {} | {}"
        ).format(
            quantity, m_info["LOT_SIZE"]["minQty"]
        )
    )


def initialise_markets_info():

    client = Client(CONFIG.API_PUB, CONFIG.API_PRI, {"timeout": 5})
    try:
        with open("market_info.json", "r") as f:
            market_info_object = json.load(f)
            # if the data was retrieved more than an hour ago we need to refresh it
            if time.time() - 3600 > float(market_info_object["TIMESTAMP"]):
                raise FileNotFoundError
            for m in CONFIG.MARKETS:
                if m not in market_info_object.keys():
                    raise FileNotFoundError

            market_info = market_info_object
            del market_info_object
    except FileNotFoundError:
        exchange_info = client.get_exchange_info()
        exchange_symbols = {
            element['symbol']: element for element in exchange_info['symbols']
        }
        market_info = {
            element['symbol']: dict() for element in exchange_info['symbols']
            if element['symbol'] in CONFIG.MARKETS
        }
        configured_market_length = len(CONFIG.MARKETS)
        LOGGER.info("Found {} markets".format(configured_market_length))

        for index, market in enumerate(CONFIG.MARKETS):
            LOGGER.info("Retrieving market data {} of {} {}".format(
                index + 1, configured_market_length, market
                )
            )

            symbol = exchange_symbols[market]

            # We do not need to spend deleting, just hold everything
            for symbol_filter in symbol["filters"]:
                market_info[market][symbol_filter["filterType"]] = symbol_filter

            # Normalize types to floats
            for filter_key in market_info[market].keys():
                for value_key in market_info[market][filter_key].keys():
                    try:
                        market_info[market][filter_key][value_key] = float(market_info[market][filter_key][value_key])
                    except ValueError:
                        pass

        market_info["TIMESTAMP"] = str(time.time())
        with open("market_info.json", "w") as f:
            json.dump(market_info, f)

    return market_info
