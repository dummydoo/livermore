# The ultimate goal of reporting is to dump as much data as possible into
# a database of some sort. This should be able to track:
# - opportunities from end to end - we should uniquely identify each opportunity
#   and report against this opportunity_id in the database. For example:
#   1. Opportunity USDT > BTC > ADA > ETH > USDT detected - id 12334, time 123232232.2322211 version: 1.0.1b
#   2. Opportunity 12334 sent to Executor at 123232232.252211 version: 1.0.1b
#   3. Opportunity 12334 received by Executor at 123232232.2722211 version: 1.0.1b
#   4. Opportunity:12334 Trade BUY BTCUSDT Q: 0.05320000 P:5534.333 at 123232232.2822211 version: 1.0.1b
#   10. Opportunity: 12334 profit: $0.23 at 123232232.5822211 version: 1.0.1b
#   etc
#   This will allow us to build dashboards to monitor performance over time (Apache superset)

import os
import threading
import multiprocessing

from sqlalchemy.orm import relationship, sessionmaker


from app import const
from app import models
import config as Config

ENVIRONMENT = os.getenv("ENVIRONMENT", "dry")
config = Config.get_config(ENVIRONMENT)



def db_write_worker(process_id, write_queue):
    dbc = models.make_livermore_session()
    while True:
        message = write_queue.get(block=True)

        if message["obj_type"] == const.OBJ_TYPE_OPPPORTUNITY:
            message_instance = models.Opportunity(
                version=config.VERSION,
                path=message["path"],
                timestamp=message["timestamp"],
                projected_profit=message["path_profit"],
                projected_profit_percent= round(
                    float(message["path_profit"]) / float(message["max_q_fiat"])
                    * 100, 3
                ),
                required_fiat_quantity=message["max_q_fiat"],

                opportunity_tag=message["opportunity_tag"],
            )

        if message["obj_type"] == const.OBJ_TYPE_EVENT:
            message_instance = models.Event(
                event_type=message["event"],
                timestamp=message["timestamp"],
                opportunity_tag=message["opportunity_tag"],
            )

        if message["obj_type"] == const.OBJ_TYPE_TRADE:
            if "trades" in message:
                message_instance = []
                for t in message["trades"]:
                    my_trade = models.Trade(
                        timestamp=t["timestamp"],
                        exchange=t["exchange"],
                        market=t["market"],
                        order_type=t["order_type"],
                        side=t["side"],
                        price=t["price"],
                        quantity=t["quantity"],
                        fills=t["fills"],
                        status=t["status"],
                        exchange_order_id=t["orderId"],
                        opportunity_tag=t["opportunity_tag"],
                    )
                    nessage_instance.append(my_trade)
            else:
                message_instance = models.Trade(
                    timestamp=message["timestamp"],
                    exchange=message["exchange"],
                    market=message["market"],
                    order_type=message["order_type"],
                    side=message["side"],
                    price=message["price"],
                    quantity=message["quantity"],
                    fills=message["fills"],
                    status=message["status"],
                    exchange_order_id=message["orderId"],
                    opportunity_tag=message["opportunity_tag"],
                )

        if message["obj_type"] == const.OBJ_TYPE_RESULT:
            message_instance = models.OpportunityResult(
                actual_profit=message["profit"],
                opportunity_tag = message["opportunity_tag"],
            )

        try:
            dbc.add(message_instance)
            dbc.commit()
        except Exception as e:
            print("Error in database write: {}".format(e))
            import pdb
            pdb.set_trace()


def reporting_loop(pullpipe):
    write_queue = multiprocessing.Queue()
    write_threads = []

    for i in range(10):
        my_thread = threading.Thread(
            target=db_write_worker, args=(i, write_queue)
        )
        write_threads.append(my_thread)

    for t in write_threads:
        t.start()

    while True:
        msg = pullpipe.get()
        write_queue.put(msg)
