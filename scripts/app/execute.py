import json
from app import const
from app import utils
from app.exceptions import NoMarketError, TooSlowException

from binance.client import Client
from binance.exceptions import BinanceAPIException

SELL = const.SELL_ORDER_DIRECTION
BUY = const.BUY_ORDER_DIRECTION

from config import CONFIG
from app.const import ENVIRONMENT

import logging

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

def execute_loop(execute_queue, report_queue, market_info, this_ip=None):
    client = Client(CONFIG.API_PUB, CONFIG.API_PRI)

    which_order = {
        "dry": client.create_test_order,
        "production": client.create_order,
    }

    make_order = which_order["production"]
    nwmon = utils.SimpleNwmon()

    while True:
        try:
            execorder = json.loads(execute_queue.get(False))
        except Exception as e:
            continue
        if execorder["type"] == "SHUTDOWN":
            quit()

        if "rates" not in execorder:
            continue

        limits_ok = nwmon.can_complete_path(len(execorder["path"]))
        if not limits_ok: continue

        rates = execorder["rates"]
        orders = []

        EXPECTED_PATH = True
        # for loops are slow, use a while len trades -1 or something
        for trade in execorder["path"]:
            # determine the quantity dependant on the previous quantities
            this_base, this_quote = utils.give_base_quote(trade["market"])
            if len(orders) > 0:
                prev_base, prev_quote = utils.give_base_quote(orders[-1]["symbol"])


                if this_base == prev_base:
                    this_quantity = float(orders[-1]["executedQty"])
                else:
                    # we need to work out the order quantity based on the
                    # previously executed quantities.
                    if trade["direction"] == BUY:
                        # previously_executed / base/quote rate
                        this_quantity = utils.closest_tradeable_quantity(
                            market_info[trade["market"]],
                            float(orders[-1]["executedQty"])
                            / rates[this_base][this_quote],
                        )
                    if trade["direction"] == SELL:
                        # prev qty * avg_price / base/quote rate
                        exec_prices = [
                            float(execorder["qty"]) * float(execorder["price"])
                            for x in orders[-1]["fills"]
                        ]
                        avg_exec_price = round(
                            sum(exec_prices) / float(orders[-1]["executedQty"]), 8
                        )
                        # * for sell not /
                        this_quantity = (
                            float(orders[-1]["executedQty"])
                            * avg_exec_price
                            * rates[this_base][this_quote]
                        )
                        this_quantity = utils.closest_tradeable_quantity(
                            market_info[trade["market"]], this_quantity
                        )
            else:
                this_quantity = float(execorder["quantity"])

            try:
                order = make_order(
                    symbol=trade["market"], side=trade["direction"],
                    type="LIMIT",
                    quantity=utils.closest_tradeable_quantity(
                        market_info[trade["market"]], this_quantity
                    ),
                    price=str(round(rates[this_base][this_quote], 8)),
                    timeInForce=("FOK"), # Fill immediately or cancel
                    newOrderRespType="FULL",
                )

                if order["status"] == "FILLED":
                    orders.append(order)
                    nwmon.iterate_order()
                    continue
                else:
                    nwmon.iterate_order()
                    raise TooSlowException("Too slow.")


            except (BinanceAPIException, TooSlowException, Exception) as e:
                # should log error
                EXPECTED_PATH = False

                if len(orders) > 0:
                    prev_base, prev_quote = utils.give_base_quote(orders[-1]["symbol"])

                    direction = orders[-1]["side"]
                    if direction == BUY:
                        currency = prev_base
                    if direction == SELL:
                        currency = prev_quote

                    # membership check quicker if config.ALL_MARKETS was a dict
                    if currency + "USDT" not in config.ALL_MARKETS:
                        order = order_method(
                            symbol=currency + "BTC",
                            side=SELL,
                            type="MARKET",
                            quantity=closest_tradeable_quantity(
                                market_info[str(currency + "BTC")],
                                float(orders[-1]["executedQty"])
                            ),
                            newOrderRespType="FULL",
                        )

                        # Next currency will be in > BTC to USDT
                        currency = "BTC"
                        orders.append(order)
                        nwmon.iterate_order()


                    order = order_method(
                        symbol=currency + "USDT",
                        side=SELL,
                        type="MARKET",
                        quantity=closest_tradeable_quantity(
                            market_info[str(currency + "USDT")],
                            float(orders[-1]["executedQty"]),
                        ),
                        newOrderRespType="FULL",
                    )

                    orders.append(order)
                    nwmon.iterate_order()


                # this break will exit the for each trade in trades loop
                # but finally will still be executed.
                break  # cancel this path

            finally:
                # calculate profit
                input_q = execorder["quantity"]
                output_q = 0


                if len(orders) > 1:
                    for fill in orders[-1]["fills"]:
                        # Commission will always be the source
                        proceeds = proceeds + float(fill["price"]) * float(fill["qty"])

                    profit = output_q - input_q
                    profit_percent = proit / input_q * 100
                else:
                    profit = 0
                    profit_percent = 0
                    proceeds = exec_prices["initial_quantity"]

                result = {
                    "type": const.EXECUTE_RESULT_TYPE,
                    "obj_type": const.OBJ_TYPE_RESULT,
                    "path": execorder["path"],
                    "orders": orders,
                    "completed_path": EXPECTED_PATH,
                    "profit": profit,
                    "profit_percent": profit_percent,
                    "opportunity_tag": execorder["opportunity_tag"]
                }

                report_queue.put(result)
                execute_queue.put(result)
