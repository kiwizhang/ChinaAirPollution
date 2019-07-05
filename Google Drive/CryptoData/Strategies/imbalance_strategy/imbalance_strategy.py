import requests
import time
import bitmex
import json
from logging.handlers import TimedRotatingFileHandler
import logging
import sys
import traceback
from datetime import datetime

API_KEY = "v0o-HTtAvn8Ihkzm8ymnyk2h"
API_SECRET = "lEbs4fitsr2uRI0c4cDRIy0Picx__Xx6Kt_lR5IPgWpLcgtX"
bot_url = "http://localhost:5000/signal"
LOG_FILENAME = 'imbalance_strategy_test.log'
timeHandler = TimedRotatingFileHandler(LOG_FILENAME, when="midnight", interval=1)
formatter = logging.Formatter('[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s',
                              '%m-%d %H:%M:%S')
timeHandler.setFormatter(formatter)
logging.basicConfig(level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S', handlers=[timeHandler, logging.StreamHandler(sys.stdout)])


class ImbalanceStrategy:
    LOG_FILENAME = 'imbalance_strategy.log'
    timeHandler = TimedRotatingFileHandler(LOG_FILENAME, when="midnight", interval=1)
    formatter = logging.Formatter('[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s',
                                  '%m-%d %H:%M:%S')
    timeHandler.setFormatter(formatter)
    logging.basicConfig(level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S', handlers=[timeHandler])

    def __init__(self):
        self.client = bitmex.bitmex(
            test=False,
            api_key="v0o-HTtAvn8Ihkzm8ymnyk2h",
            api_secret="lEbs4fitsr2uRI0c4cDRIy0Picx__Xx6Kt_lR5IPgWpLcgtX"
        )
        self.webhook_url = "https://hooks.slack.com/services/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"
        self.total_profit = 0
        self.num_pos_tx = 0
        self.num_neg_tx = 0
        self.order_state = None
        self.price_unit = 0.0000001
        self.digit = 7
        self.filled_price = None
        self.imbalance = None
        self.lowest_ask = None
        self.highest_bid = None
        self.order_id = None
        self.stop_loss = 0.01
        self.pair = "EOSU19"
        self.multiplier = 0.5
        self.max_imbalance = 20

    def run_strategy(self):
        while True:
            time.sleep(5)
            while self.order_state is None:
                time.sleep(5)
                self.get_imbalance()
                if self.imbalance < 0.1:
                    short_order_price = self.lowest_ask + round(min(self.max_imbalance, (1/self.imbalance)) * self.price_unit * self.multiplier, self.digit)
                    print(self.lowest_ask)
                    # print((1/self.imbalance) * self.price_unit * 2)
                    print(short_order_price)
                    status_code, dummy_price, self.order_id = self.place_order(short_order_price, "short","Limit", str(int(time.time())))
                    if status_code != 200:
                        break
                    self.order_state = "pending"
                    msg = "imbalance: " + str(self.imbalance) + ", placed limit short at " + str(short_order_price)
                    logging.info(msg)
                    self.send_to_slack(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ":" + msg)
                    while True:
                        time.sleep(5)
                        self.get_imbalance()
                        if self.get_order_status(self.order_id) == "Filled":
                            self.order_state = "filled_short"
                            self.filled_price = short_order_price
                            msg = "limit short filled at " + str(short_order_price)
                            logging.info(msg)
                            self.send_to_slack(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ":" + msg)
                            break
                        elif self.imbalance > 10:
                            if not self.cancel_order(self.order_id):
                                break
                            self.order_state = None
                            msg = "imbalance: " + str(self.imbalance) + ", cancelled limit short"
                            logging.info(msg)
                            self.send_to_slack(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ":" + msg)
                            break
                elif self.imbalance > 10:
                    long_order_price = self.highest_bid - round(min(self.max_imbalance, self.imbalance) * self.price_unit * self.multiplier, self.digit)
                    print(self.highest_bid)
                    # print(abs(self.imbalance) * self.price_unit * 2)
                    print(long_order_price)
                    status_code, dummy_price, self.order_id = self.place_order(long_order_price, "long", "Limit", str(int(time.time())))
                    if status_code != 200:
                        break
                    self.order_state = "pending"
                    msg = "imbalance: " + str(self.imbalance) + ", placed limit long at " + str(long_order_price)
                    logging.info(msg)
                    self.send_to_slack(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ":" + msg)
                    while True:
                        time.sleep(5)
                        self.get_imbalance()
                        if self.get_order_status(self.order_id) == "Filled":
                            self.order_state = "filled_long"
                            self.filled_price = long_order_price
                            msg = "limit long filled at " + str(long_order_price)
                            logging.info(msg)
                            self.send_to_slack(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ":" + msg)
                            break
                        elif self.imbalance < 0.1:
                            if not self.cancel_order(self.order_id):
                                break
                            self.order_state = None
                            self.filled_price = None
                            self.order_id = None
                            msg = "imbalance: " + str(self.imbalance) + ", cancelled limit long"
                            logging.info(msg)
                            self.send_to_slack(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ":" + msg)
                            break

            while self.order_state == "filled_long":
                time.sleep(5)
                self.get_imbalance()
                if self.highest_bid < self.filled_price * (1 - self.stop_loss):
                    status_code, market_close_long_price, dummy_id = self.place_order(self.highest_bid, "close_long", "Market", str(int(time.time())))
                    profit = market_close_long_price - self.filled_price
                    self.total_profit += profit
                    self.order_state = None
                    self.filled_price = None
                    self.order_id = None
                    msg = "stop loss, placed market close_long at " + str(market_close_long_price) + "\nprofit: " + str(profit) + " total_profit: " + str(self.total_profit)
                    logging.info(msg)
                    self.send_to_slack(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ":" + msg)
                    break
                elif self.imbalance < 0.1:
                    close_long_order_price = self.lowest_ask + round(min(self.max_imbalance, 1/self.imbalance) * self.price_unit * self.multiplier, self.digit)
                    status_code, dummy_price, self.order_id = self.place_order(close_long_order_price, "close_long", "Limit", str(int(time.time())))
                    if status_code != 200:
                        break
                    self.order_state = "pending"
                    msg = "imbalance: " + str(self.imbalance) + ", placed limit close_long at " + str(close_long_order_price)
                    logging.info(msg)
                    self.send_to_slack(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ":" + msg)
                    while True:
                        time.sleep(5)
                        imbalance = self.get_imbalance()
                        if self.get_order_status(self.order_id) == "Filled":
                            profit = close_long_order_price - self.filled_price
                            self.total_profit += profit
                            self.order_state = None
                            self.filled_price = None
                            self.order_id = None
                            msg = "closed long filled at " + str(close_long_order_price) + " profit: " + str(profit) + " total_profit: " + str(self.total_profit)
                            logging.info(msg)
                            self.send_to_slack(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ":" + msg)
                            break
                        elif imbalance > 10:
                            if not self.cancel_order(self.order_id):
                                break
                            status_code, market_close_long_price, dummy_id = self.place_order(self.lowest_ask, "close_long", "Market", str(int(time.time())))
                            profit = market_close_long_price - self.filled_price
                            self.total_profit += profit
                            self.order_state = None
                            self.filled_price = None
                            self.order_id = None
                            msg = "imbalance: " + str(self.imbalance) + ", cancelled limit close_long and placed market close_long at " + str(market_close_long_price) + " profit: " + str(profit) + " total_profit: " + str(self.total_profit)
                            logging.info(msg)
                            self.send_to_slack(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ":" + msg)
                            break

            while self.order_state == "filled_short":
                time.sleep(5)
                self.get_imbalance()
                if self.lowest_ask > self.filled_price * (1 + self.stop_loss):
                    status_code, market_close_short_price, dummy_id = self.place_order(self.lowest_ask, "close_short", "Market", str(int(time.time())))
                    profit = self.filled_price - market_close_short_price
                    self.total_profit += profit
                    self.order_state = None
                    self.filled_price = None
                    self.order_id = None
                    msg = "stop loss, placed market close_short at " +  str(market_close_short_price) + " profit: " + str(profit) + " total_profit: " + str(self.total_profit)
                    logging.info(msg)
                    self.send_to_slack(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ":" + msg)
                    break
                elif self.imbalance > 10:
                    close_short_order_price = self.highest_bid - round(min(self.max_imbalance, self.imbalance) * self.price_unit * self.multiplier, self.digit)
                    status_code, dummy_price, self.order_id = self.place_order(close_short_order_price, "close_short", "Limit", str(int(time.time())))
                    if status_code != 200:
                        break
                    self.order_state = "pending"
                    msg = "imbalance: " + str(self.imbalance) + ", placed limit close_short at " + str(close_short_order_price)
                    logging.info(msg)
                    self.send_to_slack(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ":" + msg)
                    while True:
                        time.sleep(5)
                        self.get_imbalance()
                        if self.get_order_status(self.order_id) == "Filled":
                            profit = self.filled_price - close_short_order_price
                            self.total_profit += profit
                            self.order_state = None
                            self.filled_price = None
                            self.order_id = None
                            msg = "close_short filled at " + str(close_short_order_price) + " profit: " + str(profit) + " total_profit: " + str(self.total_profit)
                            logging.info(msg)
                            self.send_to_slack(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ":" + msg)
                            break
                        elif self.imbalance < 0.1:
                            if not self.cancel_order(self.order_id):
                                break
                            status_code, market_close_short_price, dummy_id = self.place_order(self.lowest_ask, "close_short", "Market", str(int(time.time())))
                            profit = self.filled_price - market_close_short_price
                            self.total_profit += profit
                            self.order_state = None
                            self.filled_price = None
                            self.order_id = None
                            msg = "imbalance: " + str(self.imbalance) + ", cancelled limit close_short and placed market close_short at " + str(market_close_short_price) + " profit: " + str(profit) + " total_profit: " + str(self.total_profit)
                            logging.info(msg)
                            self.send_to_slack(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ":" + msg)
                            break

    def send_to_slack(self, msg):

        slack_data = {'text': msg}

        response = requests.post(
            self.webhook_url, data=json.dumps(slack_data),
            headers={'Content-Type': 'application/json'}
        )
        if response.status_code != 200:
            logging.error(
                'Request to slack returned an error %s, the response is:\n%s'
                % (response.status_code, response.text)
            )
            pass


    def place_order(self, price, side, type, order_id):
        amount = 1
        response = []
        if type == "Market":
            price = None
        try:
            if (side == "close_short"):
                response = self.client.Order.Order_new(
                    symbol=self.pair,
                    ordType=type,
                    price = price,
                    side="Buy",
                    execInst="Close",
                    orderQty=amount,
                    clOrdID=order_id).result()

            elif (side == "close_long"):
                response = self.client.Order.Order_new(
                    symbol=self.pair,
                    ordType=type,
                    price = price,
                    side="Sell",
                    execInst="Close",
                    orderQty=amount,
                    clOrdID=order_id).result()

            elif (side == "short"):
                response = self.client.Order.Order_new(
                    symbol=self.pair,
                    ordType=type,
                    price=price,
                    side="Sell",
                    orderQty=amount,
                    clOrdID=order_id).result()

            elif (side == "long"):
                response = self.client.Order.Order_new(
                    symbol=self.pair,
                    ordType=type,
                    price=price,
                    side="Buy",
                    orderQty=amount,
                    clOrdID=self.order_id).result()
        except Exception as e:
            logging.error(e)
            logging.error(e.__dict__)
            return e.__dict__['status_code'], 0, order_id
        logging.info("response: " + str(response[0]))
        return response[1].status_code, response[0]['price'], order_id


    def cancel_order(self, order_id):
        try:
            response = self.client.Order.Order_cancel(clOrdID=order_id).result()[0]
            logging.info(str(response))
            return True
        except Exception as e:
            logging.error(e)
            return False

    def get_imbalance(self):
        orderbook = []
        try:
            orderbook = self.client.OrderBook.OrderBook_getL2(symbol=self.pair).result()[0]
        except Exception as ex:
            logging.error(traceback.format_exc())
            print(traceback.format_exc())
            pass
        sell_list = []
        buy_list = []
        sell_size = 0
        buy_size = 0
        for pair in orderbook:
            if pair['side'] == 'Sell':
                sell_list.append(str(pair["price"]) + "," + str(pair["size"]))
            elif pair['side'] == 'Buy':
                buy_list.append(str(pair["price"]) + "," + str(pair["size"]))

        for i in range(10):
            sell_size = float(sell_list[-(i + 1)].split(",")[1]) * (10 - i)/10
            buy_size = float(buy_list[i].split(",")[1]) * (10 - i)/10
        try:
            lowest_ask = float(sell_list[-1].split(",")[0])
            # lowest_ask_size = float(sell_list[-1].split(",")[1])
            highest_bid = float(buy_list[0].split(",")[0])
            # highest_bid_size = float(buy_list[0].split(",")[1])
            self.lowest_ask = lowest_ask
            self.highest_bid = highest_bid
            self.imbalance = sell_size / buy_size
            return lowest_ask, highest_bid
        except Exception as ex:
            logging.error(ex)
            logging.error(traceback.format_exc())

    def get_order_status(self, order_id):
        order_list = self.client.Order.Order_getOrders(symbol=self.pair,count=500).result()[0]
        for order in order_list:
            if order["clOrdID"] == order_id:
                return order["ordStatus"]
        return None


if __name__ == "__main__":
    try:
        imbalance_strategy = ImbalanceStrategy()
        imbalance_strategy.run_strategy()
    except Exception as ex:
        logging.error(traceback.format_exc())
        pass







