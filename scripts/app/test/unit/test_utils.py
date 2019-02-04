import json
import unittest
import collections
import time

from app import utils
from app import const


with open("app/test/data/graph.json", "r") as f:
    graph = json.load(f)
with open("app/test/data/rates.json", "r") as f:
    rates = json.load(f)
with open("app/test/data/markets.json", "r") as f:
    market_info = json.load(f)
with open("app/test/data/trades.json", "r") as f:
    trade_example = json.load(f)

# orders=[{'origQty': '0.08000000', 'executedQty': '0.08000000', 'price': '0.00000000', 'status': 'FILLED', 'timeInForce': 'GTC', 'side': 'BUY', 'transactTime': 1530570111594, 'orderId': 2510608, 'fills': [{'commissionAsset': 'BNB', 'tradeId': 351597, 'price': '16.72800000', 'commission': '0.00004582', 'qty': '0.08000000'}], 'type': 'MARKET', 'clientOrderId': 'HMS7C8aYx4OMxdvmAvCvND', 'symbol': 'ETCUSDT'}]
#
# exec_prices = [float(x["qty"]) * float(x["price"]) for x in orders[-1]["fills"]]
# avg_exec_price = round(sum(exec_prices) / float(orders[-1]["executedQty"]), 8)
# print(avg_exec_price)


class TestSimpleNwmon(unittest.TestCase):

    def test_too_many_orders_this_second(self):
        nwmon = utils.SimpleNwmon()
        for i in range(7):
            nwmon.iterate_order()

        self.assertFalse(nwmon.can_complete_path(4))

    def test_too_many_orders_today(self):
        nwmon = utils.SimpleNwmon()
        for i in range(99995):
            nwmon.iterate_order()

        time.sleep(1)
        self.assertTrue(nwmon.can_complete_path(5))

        for i in range(10):
            nwmon.iterate_order()

        self.assertFalse(nwmon.can_complete_path(1))


class TestGiveBaseQuote(unittest.TestCase):
    def test_one(self):
        b, q = utils.give_base_quote("BTCUSDT")
        self.assertEqual(b, "BTC")
        self.assertEqual(q, "USDT")

    def test_two(self):
        b, q = utils.give_base_quote("BNBUSDT")
        self.assertEqual(b, "BNB")
        self.assertEqual(q, "USDT")

    def test_three(self):
        b, q = utils.give_base_quote("BNBETH")
        self.assertEqual(b, "BNB")
        self.assertEqual(q, "ETH")

    def test_four(self):
        b, q = utils.give_base_quote("BTCCHF")
        self.assertEqual(b, "BTC")
        self.assertEqual(q, "CHF")

    def test_five(self):
        b, q = utils.give_base_quote("BTCGBP")
        self.assertEqual(b, "BTC")
        self.assertEqual(q, "GBP")

    def test_all(self):
        for m in ALL_MARKETS:
            b, q = utils.give_base_quote(m)
            self.assertTrue(b != "")
            self.assertIn(q, ["ETH", "BTC", "USDT", "BNB"])

class TestGivePairMarketDirection(unittest.TestCase):
    test_markets = market_info.keys()

    def test_BTCUSDT(self):
        base, quote = utils.give_base_quote("BTCUSDT")

        # quote to base is a buy
        market, dir = utils.give_pair_market_direction(
            TestGivePairMarketDirection.test_markets, quote, base
        )

        self.assertEqual(market, "BTCUSDT")
        self.assertEqual(dir, const.BUY_ORDER_DIRECTION)

        # base to quote is a sell
        market, dir = utils.give_pair_market_direction(
            TestGivePairMarketDirection.test_markets, base, quote
        )

        self.assertEqual(market, "BTCUSDT")
        self.assertEqual(dir, const.SELL_ORDER_DIRECTION)

        market, dir = utils.give_pair_market_direction(
            TestGivePairMarketDirection.test_markets, base, quote
        )

        self.assertEqual(market, "BTCUSDT")
        self.assertEqual(dir, const.SELL_ORDER_DIRECTION)

    def test_ETHBTC(self):
        base, quote = utils.give_base_quote("ETHBTC")
        market, dir = utils.give_pair_market_direction(
            TestGivePairMarketDirection.test_markets, quote, base
        )

        self.assertEqual(market, "ETHBTC")
        self.assertEqual(dir, const.BUY_ORDER_DIRECTION)

        base, quote = utils.give_base_quote("ETHBTC")
        market, dir = utils.give_pair_market_direction(
            TestGivePairMarketDirection.test_markets, base, quote
        )

        self.assertEqual(market, "ETHBTC")
        self.assertEqual(dir, const.SELL_ORDER_DIRECTION)


class TestGiveSourceValue(unittest.TestCase):
    def test_currency_with_direct_link_to_source(self):
        # 1 CDCN is worth 10 cents, so 1000 CDNC = 100. USDT
        rates = collections.defaultdict(dict)
        rates["BTC"]["USDT"] = 1000.00
        rates["USDT"]["BTC"] = 0.001

        rates["USDT"]["CDCN"] = 10.00
        rates["CDCN"]["USDT"] = 0.1
        r = utils.give_source_value("CDCN", 1000, rates)
        self.assertEqual(r, 100.0)

    def test_currency_with_tenuous_link_to_source(self):
        """
        Test we get the correct value (in quote, default usdt) when there is
        not a direct link between currencies. IE when there is no vertex
        connecting them.
        """
        rates = collections.defaultdict(dict)

        rates["BTC"]["USDT"] = 1000.0
        rates["USDT"]["BTC"] = 0.001

        rates["TSTN"]["BTC"] = 0.1
        rates["BTC"]["TSTN"] = 1.0

        r = utils.give_source_value("TSTN", 100, rates)
        self.assertEqual(r, 10000.00)


class TestGiveMaxQuantityThroughPath(unittest.TestCase):
    def test_short_path(self):
        pass

    def test_long_path(self):
        pass


class TestDirectionQuantity(unittest.TestCase):
    def test_buy(self):
        pass

    def test_sell(self):
        pass

    def test_buy_sell(self):
        pass

    def test_buy_buy_sell(self):
        pass

    def test_buy_sell_buy_sell(self):
        pass


class TestAddToGraph(unittest.TestCase):
    def test_add_to_graph(self):
        return
        from app import utils as utils
        import collections

        graph = collections.defaultdict(dict)
        rates = collections.defaultdict(dict)

        utils.add_to_graph(graph, rates, "BTC", 6000.00, "USDT", 0.005)

        # self.assert(graph["BTC"]["USDT"] == math.log10(6000.00))

        print(graph)
        print(rates)
        # TestAddToGraph.test_add_to_graph(0)


class TestClosestTradeableQuantity(unittest.TestCase):
    MARKET_DATA = {
        "STRATBTC": {
            "PRICE_FILTER": {
                "minPrice": 2.33e-05,
                "maxPrice": 0.002325,
                "tickSize": 1e-07,
            },
            "LOT_SIZE": {"minQty": 0.01, "maxQty": 90000000.0, "stepSize": 0.01},
        },
        "VENBTC": {
            "PRICE_FILTER": {
                "minPrice": 1e-08,
                "maxPrice": 100000.0,
                "tickSize": 1e-08,
            },
            "LOT_SIZE": {"minQty": 1.0, "maxQty": 90000000.0, "stepSize": 1.0},
        },
        "SALTBTC": {
            "PRICE_FILTER": {
                "minPrice": 6.9e-06,
                "maxPrice": 0.000682,
                "tickSize": 1e-07,
            },
            "LOT_SIZE": {"minQty": 0.01, "maxQty": 90000000.0, "stepSize": 0.01},
        },
        "VENBNB": {
            "PRICE_FILTER": {
                "minPrice": 0.0151,
                "maxPrice": 1.5015,
                "tickSize": 0.0001,
            },
            "LOT_SIZE": {"minQty": 0.01, "maxQty": 10000000.0, "stepSize": 0.01},
        },
        "XVGBTC": {
            "PRICE_FILTER": {
                "minPrice": 2.4e-07,
                "maxPrice": 2.37e-05,
                "tickSize": 1e-08,
            },
            "LOT_SIZE": {"minQty": 1.0, "maxQty": 90000000.0, "stepSize": 1.0},
        },
        "BNBBTC": {
            "PRICE_FILTER": {
                "minPrice": 0.0001547,
                "maxPrice": 0.015466,
                "tickSize": 1e-07,
            },
            "LOT_SIZE": {"minQty": 0.01, "maxQty": 90000000.0, "stepSize": 0.01},
        },
        "NEOUSDT": {
            "PRICE_FILTER": {"minPrice": 1.985, "maxPrice": 198.5, "tickSize": 0.001},
            "LOT_SIZE": {"minQty": 0.001, "maxQty": 10000000.0, "stepSize": 0.001},
        },
        "IOTAUSDT": {
            "PRICE_FILTER": {"minPrice": 0.063, "maxPrice": 6.3, "tickSize": 0.0001},
            "LOT_SIZE": {"minQty": 0.01, "maxQty": 10000000.0, "stepSize": 0.01},
        },
        "TRXBTC": {
            "PRICE_FILTER": {
                "minPrice": 3.7e-07,
                "maxPrice": 3.7e-05,
                "tickSize": 1e-08,
            },
            "LOT_SIZE": {"minQty": 1.0, "maxQty": 90000000.0, "stepSize": 1.0},
        },
        "DASHBTC": {
            "PRICE_FILTER": {
                "minPrice": 0.003105,
                "maxPrice": 0.31042,
                "tickSize": 1e-06,
            },
            "LOT_SIZE": {"minQty": 0.001, "maxQty": 10000000.0, "stepSize": 0.001},
        },
        "EOSUSDT": {
            "PRICE_FILTER": {
                "minPrice": 0.6186,
                "maxPrice": 61.8585,
                "tickSize": 0.0001,
            },
            "LOT_SIZE": {"minQty": 0.01, "maxQty": 10000000.0, "stepSize": 0.01},
        },
        "IOTABNB": {
            "PRICE_FILTER": {
                "minPrice": 0.00602,
                "maxPrice": 0.6018,
                "tickSize": 1e-05,
            },
            "LOT_SIZE": {"minQty": 0.1, "maxQty": 90000000.0, "stepSize": 0.1},
        },
        "ZRXBTC": {
            "PRICE_FILTER": {
                "minPrice": 9.48e-06,
                "maxPrice": 0.000948,
                "tickSize": 1e-08,
            },
            "LOT_SIZE": {"minQty": 1.0, "maxQty": 90000000.0, "stepSize": 1.0},
        },
        "EOSETH": {
            "PRICE_FILTER": {
                "minPrice": 0.002494,
                "maxPrice": 0.2494,
                "tickSize": 1e-06,
            },
            "LOT_SIZE": {"minQty": 0.01, "maxQty": 90000000.0, "stepSize": 0.01},
        },
        "VENETH": {
            "PRICE_FILTER": {
                "minPrice": 1e-08,
                "maxPrice": 100000.0,
                "tickSize": 1e-08,
            },
            "LOT_SIZE": {"minQty": 1.0, "maxQty": 90000000.0, "stepSize": 1.0},
        },
        "ETCUSDT": {
            "PRICE_FILTER": {
                "minPrice": 1.1698,
                "maxPrice": 116.9705,
                "tickSize": 0.0001,
            },
            "LOT_SIZE": {"minQty": 0.01, "maxQty": 10000000.0, "stepSize": 0.01},
        },
        "ZRXETH": {
            "PRICE_FILTER": {
                "minPrice": 0.00025827,
                "maxPrice": 0.0258266,
                "tickSize": 1e-08,
            },
            "LOT_SIZE": {"minQty": 1.0, "maxQty": 90000000.0, "stepSize": 1.0},
        },
        "XEMBTC": {
            "PRICE_FILTER": {
                "minPrice": 1.5e-06,
                "maxPrice": 0.0001495,
                "tickSize": 1e-08,
            },
            "LOT_SIZE": {"minQty": 1.0, "maxQty": 90000000.0, "stepSize": 1.0},
        },
        "ETCETH": {
            "PRICE_FILTER": {
                "minPrice": 0.004724,
                "maxPrice": 0.47239,
                "tickSize": 1e-06,
            },
            "LOT_SIZE": {"minQty": 0.01, "maxQty": 90000000.0, "stepSize": 0.01},
        },
        "EOSBTC": {
            "PRICE_FILTER": {
                "minPrice": 9.17e-05,
                "maxPrice": 0.0091665,
                "tickSize": 1e-07,
            },
            "LOT_SIZE": {"minQty": 0.01, "maxQty": 90000000.0, "stepSize": 0.01},
        },
        "NEOBTC": {
            "PRICE_FILTER": {
                "minPrice": 0.000294,
                "maxPrice": 0.029365,
                "tickSize": 1e-06,
            },
            "LOT_SIZE": {"minQty": 0.01, "maxQty": 100000.0, "stepSize": 0.01},
        },
        "IOTAETH": {
            "PRICE_FILTER": {
                "minPrice": 0.0002543,
                "maxPrice": 0.0254296,
                "tickSize": 1e-08,
            },
            "LOT_SIZE": {"minQty": 1.0, "maxQty": 90000000.0, "stepSize": 1.0},
        },
        "ADABTC": {
            "PRICE_FILTER": {
                "minPrice": 1.3e-06,
                "maxPrice": 0.0001297,
                "tickSize": 1e-08,
            },
            "LOT_SIZE": {"minQty": 1.0, "maxQty": 90000000.0, "stepSize": 1.0},
        },
        "WTCBTC": {
            "PRICE_FILTER": {
                "minPrice": 4.7e-05,
                "maxPrice": 0.004693,
                "tickSize": 1e-07,
            },
            "LOT_SIZE": {"minQty": 0.01, "maxQty": 90000000.0, "stepSize": 0.01},
        },
        "XRPUSDT": {
            "PRICE_FILTER": {"minPrice": 0.05643, "maxPrice": 5.643, "tickSize": 1e-05},
            "LOT_SIZE": {"minQty": 0.1, "maxQty": 90000000.0, "stepSize": 0.1},
        },
        "XRPBTC": {
            "PRICE_FILTER": {
                "minPrice": 8.35e-06,
                "maxPrice": 0.0008347,
                "tickSize": 1e-08,
            },
            "LOT_SIZE": {"minQty": 1.0, "maxQty": 90000000.0, "stepSize": 1.0},
        },
        "LTCETH": {
            "PRICE_FILTER": {
                "minPrice": 0.02461,
                "maxPrice": 2.46065,
                "tickSize": 1e-05,
            },
            "LOT_SIZE": {"minQty": 0.001, "maxQty": 10000000.0, "stepSize": 0.001},
        },
        "XMRBTC": {
            "PRICE_FILTER": {
                "minPrice": 0.00184,
                "maxPrice": 0.18398,
                "tickSize": 1e-06,
            },
            "LOT_SIZE": {"minQty": 0.001, "maxQty": 10000000.0, "stepSize": 0.001},
        },
        "ETHBTC": {
            "PRICE_FILTER": {"minPrice": 0.00367, "maxPrice": 0.367, "tickSize": 1e-06},
            "LOT_SIZE": {"minQty": 0.001, "maxQty": 100000.0, "stepSize": 0.001},
        },
        "BNBETH": {
            "PRICE_FILTER": {
                "minPrice": 0.004229,
                "maxPrice": 0.42282,
                "tickSize": 1e-06,
            },
            "LOT_SIZE": {"minQty": 0.01, "maxQty": 90000000.0, "stepSize": 0.01},
        },
        "ADAETH": {
            "PRICE_FILTER": {
                "minPrice": 3.542e-05,
                "maxPrice": 0.0035414,
                "tickSize": 1e-08,
            },
            "LOT_SIZE": {"minQty": 1.0, "maxQty": 90000000.0, "stepSize": 1.0},
        },
        "BTGBTC": {
            "PRICE_FILTER": {
                "minPrice": 0.00034,
                "maxPrice": 0.03394,
                "tickSize": 1e-06,
            },
            "LOT_SIZE": {"minQty": 0.01, "maxQty": 10000000.0, "stepSize": 0.01},
        },
        "XLMBTC": {
            "PRICE_FILTER": {
                "minPrice": 3.68e-06,
                "maxPrice": 0.0003671,
                "tickSize": 1e-08,
            },
            "LOT_SIZE": {"minQty": 1.0, "maxQty": 90000000.0, "stepSize": 1.0},
        },
        "LTCBTC": {
            "PRICE_FILTER": {
                "minPrice": 0.000902,
                "maxPrice": 0.090105,
                "tickSize": 1e-06,
            },
            "LOT_SIZE": {"minQty": 0.01, "maxQty": 100000.0, "stepSize": 0.01},
        },
        "QTUMBTC": {
            "PRICE_FILTER": {"minPrice": 6e-05, "maxPrice": 0.006, "tickSize": 1e-06},
            "LOT_SIZE": {"minQty": 0.01, "maxQty": 10000000.0, "stepSize": 0.01},
        },
        "ETHUSDT": {
            "PRICE_FILTER": {"minPrice": 24.78, "maxPrice": 2477.1, "tickSize": 0.01},
            "LOT_SIZE": {"minQty": 1e-05, "maxQty": 10000000.0, "stepSize": 1e-05},
        },
        "BCCBTC": {
            "PRICE_FILTER": {
                "minPrice": 0.007436,
                "maxPrice": 0.7436,
                "tickSize": 1e-06,
            },
            "LOT_SIZE": {"minQty": 0.001, "maxQty": 100000.0, "stepSize": 0.001},
        },
        "ETCBNB": {
            "PRICE_FILTER": {"minPrice": 0.112, "maxPrice": 11.192, "tickSize": 0.0001},
            "LOT_SIZE": {"minQty": 0.01, "maxQty": 10000000.0, "stepSize": 0.01},
        },
        "IOTABTC": {
            "PRICE_FILTER": {
                "minPrice": 9.3e-06,
                "maxPrice": 0.00093,
                "tickSize": 1e-08,
            },
            "LOT_SIZE": {"minQty": 1.0, "maxQty": 90000000.0, "stepSize": 1.0},
        },
        "BNBUSDT": {
            "PRICE_FILTER": {
                "minPrice": 1.0478,
                "maxPrice": 104.7795,
                "tickSize": 0.0001,
            },
            "LOT_SIZE": {"minQty": 0.01, "maxQty": 10000000.0, "stepSize": 0.01},
        },
        "TRXETH": {
            "PRICE_FILTER": {
                "minPrice": 1.012e-05,
                "maxPrice": 0.0010111,
                "tickSize": 1e-08,
            },
            "LOT_SIZE": {"minQty": 1.0, "maxQty": 90000000.0, "stepSize": 1.0},
        },
        "BTCUSDT": {
            "PRICE_FILTER": {
                "minPrice": 675.86,
                "maxPrice": 67585.05,
                "tickSize": 0.01,
            },
            "LOT_SIZE": {"minQty": 1e-06, "maxQty": 10000000.0, "stepSize": 1e-06},
        },
        "LTCUSDT": {
            "PRICE_FILTER": {"minPrice": 6.08, "maxPrice": 607.85, "tickSize": 0.01},
            "LOT_SIZE": {"minQty": 1e-05, "maxQty": 10000000.0, "stepSize": 1e-05},
        },
    }

ALL_MARKETS = [
    "ETHBTC",
    "LTCBTC",
    "BNBBTC",
    "NEOBTC",
    "QTUMETH",
    "EOSETH",
    "SNTETH",
    "BNTETH",
    "BCCBTC",
    "GASBTC",
    "BTCUSDT",
    "ETHUSDT",
    "HSRBTC",
    "OAXETH",
    "DNTETH",
    "MCOETH",
    "ICNETH",
    "MCOBTC",
    "WTCBTC",
    "WTCETH",
    "LRCBTC",
    "LRCETH",
    "QTUMBTC",
    "YOYOBTC",
    "OMGBTC",
    "OMGETH",
    "ZRXBTC",
    "ZRXETH",
    "STRATBTC",
    "STRATETH",
    "SNGLSBTC",
    "SNGLSETH",
    "BQXBTC",
    "BQXETH",
    "KNCBTC",
    "KNCETH",
    "FUNBTC",
    "FUNETH",
    "SNMBTC",
    "SNMETH",
    "NEOETH",
    "IOTABTC",
    "IOTAETH",
    "LINKBTC",
    "LINKETH",
    "XVGBTC",
    "XVGETH",
    "MDABTC",
    "MDAETH",
    "MTLBTC",
    "MTLETH",
    "SUBBTC",
    "SUBETH",
    "EOSBTC",
    "SNTBTC",
    "ETCETH",
    "ETCBTC",
    "MTHBTC",
    "MTHETH",
    "ENGBTC",
    "ENGETH",
    "DNTBTC",
    "ZECBTC",
    "ZECETH",
    "BNTBTC",
    "ASTBTC",
    "ASTETH",
    "DASHBTC",
    "DASHETH",
    "OAXBTC",
    "ICNBTC",
    "BTGBTC",
    "BTGETH",
    "EVXBTC",
    "EVXETH",
    "REQBTC",
    "REQETH",
    "VIBBTC",
    "VIBETH",
    "HSRETH",
    "TRXBTC",
    "TRXETH",
    "POWRBTC",
    "POWRETH",
    "ARKBTC",
    "ARKETH",
    "YOYOETH",
    "XRPBTC",
    "XRPETH",
    "MODBTC",
    "MODETH",
    "ENJBTC",
    "ENJETH",
    "STORJBTC",
    "STORJETH",
    "KMDBTC",
    "KMDETH",
    "RCNBTC",
    "RCNETH",
    "NULSBTC",
    "NULSETH",
    "RDNBTC",
    "RDNETH",
    "XMRBTC",
    "XMRETH",
    "DLTBTC",
    "DLTETH",
    "AMBBTC",
    "AMBETH",
    "BCCETH",
    "BCCUSDT",
    "BATBTC",
    "BATETH",
    "BCPTBTC",
    "BCPTETH",
    "ARNBTC",
    "ARNETH",
    "GVTBTC",
    "GVTETH",
    "CDTBTC",
    "CDTETH",
    "GXSBTC",
    "GXSETH",
    "NEOUSDT",
    "POEBTC",
    "POEETH",
    "QSPBTC",
    "QSPETH",
    "BTSBTC",
    "BTSETH",
    "XZCBTC",
    "XZCETH",
    "LSKBTC",
    "LSKETH",
    "TNTBTC",
    "TNTETH",
    "FUELBTC",
    "FUELETH",
    "MANABTC",
    "MANAETH",
    "BCDBTC",
    "BCDETH",
    "DGDBTC",
    "DGDETH",
    "ADXBTC",
    "ADXETH",
    "ADABTC",
    "ADAETH",
    "PPTBTC",
    "PPTETH",
    "CMTBTC",
    "CMTETH",
    "XLMBTC",
    "XLMETH",
    "CNDBTC",
    "CNDETH",
    "LENDBTC",
    "LENDETH",
    "WABIBTC",
    "WABIETH",
    "LTCETH",
    "LTCUSDT",
    "TNBBTC",
    "TNBETH",
    "WAVESBTC",
    "WAVESETH",
    "GTOBTC",
    "GTOETH",
    "ICXBTC",
    "ICXETH",
    "OSTBTC",
    "OSTETH",
    "ELFBTC",
    "ELFETH",
    "AIONBTC",
    "AIONETH",
    "NEBLBTC",
    "NEBLETH",
    "BRDBTC",
    "BRDETH",
    "EDOBTC",
    "EDOETH",
    "WINGSBTC",
    "WINGSETH",
    "NAVBTC",
    "NAVETH",
    "LUNBTC",
    "LUNETH",
    "TRIGBTC",
    "TRIGETH",
    "APPCBTC",
    "APPCETH",
    "VIBEBTC",
    "VIBEETH",
    "RLCBTC",
    "RLCETH",
    "INSBTC",
    "INSETH",
    "PIVXBTC",
    "PIVXETH",
    "IOSTBTC",
    "IOSTETH",
    "CHATBTC",
    "CHATETH",
    "STEEMBTC",
    "STEEMETH",
    "NANOBTC",
    "NANOETH",
    "VIABTC",
    "VIAETH",
    "BLZBTC",
    "BLZETH",
    "AEBTC",
    "AEETH",
    "RPXBTC",
    "RPXETH",
    "NCASHBTC",
    "NCASHETH",
    "POABTC",
    "POAETH",
    "ZILBTC",
    "ZILETH",
    "ONTBTC",
    "ONTETH",
    "STORMBTC",
    "STORMETH",
    "QTUMUSDT",
    "XEMBTC",
    "XEMETH",
    "WANBTC",
    "WANETH",
    "WPRBTC",
    "WPRETH",
    "QLCBTC",
    "QLCETH",
    "SYSBTC",
    "SYSETH",
    "GRSBTC",
    "GRSETH",
    "ADAUSDT",
    "CLOAKBTC",
    "CLOAKETH",
    "GNTBTC",
    "GNTETH",
    "LOOMBTC",
    "LOOMETH",
    "XRPUSDT",
    "BCNBTC",
    "BCNETH",
    "REPBTC",
    "REPETH",
    "TUSDBTC",
    "TUSDETH",
    "ZENBTC",
    "ZENETH",
    "SKYBTC",
    "SKYETH",
    "EOSUSDT",
    "CVCBTC",
    "CVCETH",
    "THETABTC",
    "THETAETH",
    "TUSDUSDT",
    "IOTAUSDT",
    "XLMUSDT",
    "IOTXBTC",
    "IOTXETH",
    "QKCBTC",
    "QKCETH",
    "AGIBTC",
    "AGIETH",
    "NXSBTC",
    "NXSETH",
    "DATABTC",
    "DATAETH",
    "ONTUSDT",
    "TRXUSDT",
    "ETCUSDT",
    "ICXUSDT",
    "SCBTC",
    "SCETH",
    "NPXSBTC",
    "NPXSETH",
    "VENUSDT",
    "KEYBTC",
    "KEYETH",
    "NASBTC",
    "NASETH",
]
