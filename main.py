#!/usr/bin/env python
import time
import uuid
import json
import datetime
import collections
import multiprocessing

from absl import app
from app import const
from app import execute
from app import reporting
from app import listen

from config import CONFIG

from app.paths import find_cycles
from app.listen import listen_orderbook
from app.orderbook import LimitOrderBook
from app.exceptions import QuantityTooSmallError
from app.utils import add_to_graph, give_base_quote, closest_tradeable_quantity
from app.utils import initialise_markets_info, give_base_quote
from app.utils import closest_tradeable_quantity
from app.utils import give_pair_market_direction, give_max_quantity_through_path
from app.const import WEB_SOCKETS_TOPIC_HEAD_LENGTH, WEB_SOCKETS_TOPIC_TAIL_LENGTH
from app.const import TRANSACTION_COST
from app.flags import FLAGS

from binance.client import Client
import zmq

from queue import Queue

import logging

logging.basicConfig(level=logging.INFO)

LOGGER = logging.getLogger("main")

def main(argv):

    rates = collections.defaultdict(dict)
    graph = collections.defaultdict(dict)

    orderbook_dicts = {}
    markets_info = {}

    client = Client(CONFIG.API_PUB, CONFIG.API_PRI, {"timeout": 5})

    # set up our orderbook_dicts with orderbook instances.
    # this list will be used to check that we have some data about every market
    # before executing trades.
    orderbook_dicts = {m: LimitOrderBook(m) for m in CONFIG.MARKETS}

    # Retrieve data about markets, IE minimum quantity, minimum price increment etc
    # Do the moving around before we even start the bot so that we get O(1)
    # Access later.

    executed_trades = {}

    markets_info = initialise_markets_info()
    start_time = time.time()

    execute_lock = True
    execute_trade_queue = multiprocessing.Queue()

    report_queue = multiprocessing.Queue()

    execute_process = multiprocessing.Process(
        target=execute.execute_loop,
        args=(
            execute_trade_queue,
            report_queue,
            markets_info,
            CONFIG.EXECUTE_IP,
        )
    )

    reporting_process = multiprocessing.Process(
        target=reporting.reporting_loop, args=(report_queue,)
    )

    listen_process = multiprocessing.Process(
        target=listen.listen_orderbook, args=(markets_info.keys(),)
    )

    execute_process.start()
    reporting_process.start()

    if CONFIG.MODE == const.DRY_MODE:
        listen_process.start()


    if FLAGS.input:
        raw_data_queue = Queue()
        for line in open(FLAGS.input):
            element_list = json.loads(line)
            LOGGER.info(len(element_list))
            for element in element_list:
                element[0] = element[0].encode()
                element[1] = element[1].encode()
                raw_data_queue.put(element)

        class FakeSocket(object):
            pass

        socket = FakeSocket()
        socket.recv_multipart = raw_data_queue.get_nowait
    else:
        LOGGER.info("LIVE DATA FEED")
        # zmq - subscribe to our zmq server
        ctx = zmq.Context()
        socket = ctx.socket(zmq.SUB)
        socket.connect(CONFIG.ZMQ_SOCKET)
        socket.setsockopt(zmq.SUBSCRIBE, CONFIG.ZMQ_TOPIC)
        socket.linger = 10

    b = client.get_asset_balance("USDT")
    start_bal = float(b["free"])
    current_bal = float(b["free"])

    while True:
        # check if the execute_lock is False, check for execution results, update
        # balances and profits.
        if not execute_lock:
            if not execute_trade_queue.empty():
                check_exec = execute_trade_queue.get(block=False)
            else:
                check_exec = None

            if check_exec:
                if check_exec["type"] == const.EXECUTE_RESULT_TYPE:
                    execute_lock = True
                if check_exec["type"] == const.EXECUTE_TOO_SOON_TYPE:
                    execute_lock = True

                LOGGER.info(str(check_exec))
                execute_lock = True
                # Should the execute_handler update orderbooks with trade results?
                # We have moved the market; we should be sure not to try and execute on
                # oppurtunities we've already taken.

        # We need to keep getting messages if they exist here..
        # this implementation for retrieving messages is not ideal. We should
        # receive messages until there are no more, then perform analysis, and
        # queue any trades. Then look for more messages. Instead we find one
        # message and perform analysis / trades on potentially stale info.
        # LOGGER.info("TEST")
        # LOGGER.info(markets_info.keys())

        msg = None
        try:
            topic, msg = socket.recv_multipart(zmq.NOBLOCK)
        except zmq.error.Again:
            # LOGGER.info("zmq.error.Again".format(msg))
            continue

        if not msg:
            continue

        msg = json.loads(msg.decode("utf-8"))
        topic = topic.decode("utf-8")

        # topic = (
        #     topic[WEB_SOCKETS_TOPIC_HEAD_LENGTH: -WEB_SOCKETS_TOPIC_TAIL_LENGTH]
        #     .upper()
        # )

        if not topic:
            try:
                topic = msg["market"]
            except KeyError as e:
                LOGGER.error(
                    "We weren't able to find the market for this message {}"\
                    .format(msg)
                )
                continue

        market = topic

        base, quote = give_base_quote(market)
        if market not in orderbook_dicts.keys():
            continue

        orderbook_dicts[market].update_levels_from_partial(msg)
        rate = orderbook_dicts[market].best_price["price"]

        add_to_graph(graph, rates, base, rate, quote, TRANSACTION_COST)

        # ensure all orderbooks are populated before continuing... Not a check
        # that should really be in the exec loop.
        orderbooks_populated = True
        for m, lob in orderbook_dicts.items():
            if not orderbooks_populated:
                break
            if not lob.last_update:
                orderbooks_populated = False
                LOGGER.info("{} still not populated".format(m))

        if not orderbooks_populated:
            continue

        max_q = 0
        path_profit = 0

        # find_cycles will return cycles sorted by profit multiplier, however actual
        # profit may be 0 because the quantites available are too small. We should
        # loop through arbs to see if they provide some profit.
        # this should be modified to the most profitable path we haven't run this
        # second. This implementation is PoC of this being the problem.

        for arbitrage in find_cycles(graph, rates):
            path = arbitrage["currencies"]
            trades = []

            # get trade market and directions for the path
            for i in range(len(path) - 1):
                market, direction = give_pair_market_direction(
                    CONFIG.MARKETS, path[i], path[i + 1]
                )
                trades.append({"market": market, "direction": direction})

            path_str = "".join(sorted([c["market"] for c in trades]))
            try:
                path_last_executed = executed_trades[path_str]
            except KeyError as e:
                executed_trades[path_str] = 0
                path_last_executed = executed_trades[path_str]

            if time.time() - path_last_executed < 3:
                continue

            executed_trades[path_str] = time.time()

            max_q = round(
                give_max_quantity_through_path(trades, rates, orderbook_dicts, 50), 2
            )

            # hopefully less quantity equals less risk
            if max_q > 50.0:
                max_q = 50.00

            # calculate some things
            path_return = round(max_q * arbitrage["value"], 2)
            path_profit = round(path_return - max_q, 2)
            trade_str = "->".join([x["market"] for x in trades])

            if path_profit < 0.05:
                continue
            if path_profit > 0.05:
                break

        # CHECK THE PATH ACTUALLY ADDS UP
        if max_q > 1 and path_profit > 0.01:
            # max_q IS FIAT QUANTITY. NEED CRYPTO QUANTITY.
            base, quote = give_base_quote(trades[0]["market"])
            max_q_fiat = max_q
            max_q = max_q / rates[base][quote]

            try:
                max_q = closest_tradeable_quantity(markets_info[trades[0]["market"]], max_q)
            except QuantityTooSmallError:
                LOGGER.info("QUANTITY_TOO_SMALL for market".format(trades[0]["market"]))
                continue

            # 25% is a little optimistic, let's sanity check this!
            if arbitrage["value"] > 1.25:
                LOGGER.info(
                    "SKIPPING UNREALISTIC PATH VALUE: ".format(
                        arbitrage["currencies"], arbitrage["value"]
                    )
                )
                LOGGER.info(
                    "ORDERBOOK BEST PRICES: ",
                    [orderbook_dicts[x["market"]].best_price["price"] for x in trades],
                )
                # here investigate the orderbooks for markets in the path with
                # particular emphasis on their content and last_update timestamp

            opportunity_tag = str(uuid.uuid4())
            LOGGER.info("{} {} {} {}".format(
                str(datetime.datetime.utcnow()),
                trade_str, max_q_fiat, path_profit
                )
            )
            if CONFIG.EXECUTE:
                LOGGER.info("{} {} {} {}".format(
                    str(datetime.datetime.utcnow()),
                    trade_str, max_q_fiat, path_profit
                    ))
                report_queue.put(
                    {
                        "obj_type": const.OBJ_TYPE_OPPPORTUNITY,
                        "path": str(trades),
                        "max_q_fiat": max_q_fiat,
                        "path_profit": path_profit,
                        "timestamp": time.time(),
                        "opportunity_tag": opportunity_tag
                    }
                )

                # We need a pre-execution check to ensure that the orderbooks were
                # up to date when the path was generated.

                now = time.time()
                break_execute = False
                for t in trades:
                    if (
                        now - orderbook_dicts[t["market"]].last_update
                        > CONFIG.STALE_TIMEOUT
                    ):
                        break_execute = True

                if break_execute:
                    LOGGER.info("STALE PATH")
                    LOGGER.info(str(now - orderbook_dicts[t["market"]].last_update))
                    continue

                del (now)

                # Update the balance; We've allocated this money.
                current_bal = current_bal - max_q

                # put a job onto the executor.


                if execute_lock:
                    execute_lock = False

                    execute_trade_queue.put(
                        {
                            "type": const.EXECUTE_PATH_TYPE,
                            "path": trades,
                            "rates": rates,
                            "quantity": closest_tradeable_quantity(
                                markets_info[trades[0]["market"]], max_q
                            ),
                            "initial_quantity": max_q_fiat,
                            "opportunity_tag": opportunity_tag
                        }
                    )

                    report_queue.put(
                        {
                            "obj_type": const.OBJ_TYPE_EVENT,
                            "event": const.EVENT_OPPORTUNITY_SENT_TO_EXECUTOR,
                            "timestamp": time.time(),
                            "opportunity_tag": opportunity_tag
                        }
                    )
                else:
                    continue
            else:
                report_queue.put(
                    {
                        "obj_type": const.OBJ_TYPE_OPPPORTUNITY,
                        "path": str(trades),
                        "max_q_fiat": max_q_fiat,
                        "path_profit": path_profit,
                        "timestamp": time.time(),
                        "opportunity_tag": opportunity_tag
                    }
                )
                LOGGER.info("{} {} {} {}".format(
                    str(datetime.datetime.utcnow()),
                    trade_str, max_q_fiat, path_profit
                    )
                )

if __name__ == "__main__":
    app.run(main)
