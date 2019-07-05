from binance.client import Client
from datetime import datetime
from binance.websockets import BinanceSocketManager
import time
import logging
import json
import requests
import threading
from datastore import datastore
from random import randint
from logging.handlers import TimedRotatingFileHandler

LOG_FILENAME = 'KlineSource.log'
timeHandler = TimedRotatingFileHandler(LOG_FILENAME, when="midnight", interval=1)
logging.basicConfig(level=logging.DEBUG, handlers=[timeHandler])

API_KEY = ""
API_SECRET = ""

"""
Binance Kline Data Source that provides minute level streaming data
:param : data lag needs to be specified
:return: provides minute level streaming kline data
"""
class KlineSource(threading.Thread):

    def __init__(self, threadID, name):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.asks = []
        self.bids = []
        self.combined = []
        self.cur_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.datalist = []
        self.data_lag = "5 minutes ago UTC"
        self.write_flag = True
        self.btc_usdt_flag = False
        self.eth_usdt_flag = False
        self.eth_btc_flag = True
        self.lowestAsk = 0
        self.highestBid = 0
        self.prev_bought_price = 0
        self.webhook_url = 'https://hooks.slack.com/services/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'
        self.num_tx = 0
        self.num_pos_pair = 0
        self.num_neg_pair = 0
        self.gross_profit = 0
        self.net_profit = 0
        self.num_cons_pos_pair = 0
        self.num_cons_neg_pair = 0
        self.last_profit = None
        self.fee_rate = 0.001
        self.slippage = 0.001
        self.client = Client('','') # doesn't need account and key to listen

    def process_message(self):
        """
        Collect the realtime orderbook data and save in memory
        :param msg:
        :return:
        """
        if (self.datalist == []):
            self.datalist = self.get_data(self.data_lag)

        while True:
            self.datalist.append(self.get_data("1 minute ago UTC")[0])
            self.datalist.pop(0)
            datastore.set_kline_data(self.datalist)
            logging.debug("updated kline data   ... " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            print("kline source running    ...." + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            # return self.datalist
            # try:
            #     print(self.datalist)
            #     # signal = self.get_signal(self.datalist)
            #     # logging.debug((str)(self.cur_time) + " signal: " + signal)
            #     # self.trigger_bot(signal)
            # except Exception as ex:
            #     logging.error(ex)
            #     pass
            time.sleep(60)

    def get_data(self, start_time):
        klines = self.client.get_historical_klines("BTCUSDT", Client.KLINE_INTERVAL_1MINUTE, start_time)
        flat_list = []
        for sublist in klines:
            flat_list.append(str(sublist))
        # print(flat_list)
        return flat_list

    def get_signal(self, datalist):
        """
        Apply the algorithm into the data, and output the signal
        :param datalist: the orderbook data in memory
        :return: the signal: -1, 0 or 1
        """
        # from algos import random_generator
        # algo = random_generator.random_generator()
        # return algo.main(datalist)
        signal = randint(-1, 1)
        if (signal == -1 ):
            return "sell"
        elif (signal == 1):
            return "buy"
        else:
            return "hold"

    def trigger_bot(self, signal):
        """
        Send the signal to the bot and trigger the action
        :param signal: sell, buy or hold
        :return:
        """
        if (signal == "hold"):
            return
        # print(signal)
        self.cur_time = datetime.now().strftime('%Y-%m-%d-%H:%M:%S')
        uuid = str(int(time.time()))
        cur_price = ((float)(self.lowestAsk) + (float)(self.highestBid))/2

        if (signal == "buy"):
            self.prev_bought_price = cur_price

        trade_info = self.cur_time + "," + uuid + "," + signal + "," + str(cur_price) + "," + str(self.lowestAsk) + "," + str(self.highestBid)
        logging.info(trade_info)
        # print(trade_info)
        trade_stats = self.generate_stats(signal, cur_price)
        logging.info(trade_stats)
        # print(trade_stats)
        self.send_to_slack(trade_info + "\n\n" + trade_stats)
        pass

    def generate_stats(self, signal, cur_price):
        """
        Generate the trading stats
        :param signal:
        :param cur_price:
        :return:
        """
        logging.debug("generating stats, signal: " + signal)
        print("generating stats, signal: " + signal)
        cur_profit = 0
        if (signal == "sell"):
            cur_profit = cur_price - self.prev_bought_price
            if (cur_profit >= 0):
                self.num_pos_pair += 1
                self.num_cons_pos_pair += 1
                if (self.last_profit is not None and self.last_profit < 0):
                    self.num_cons_neg_pair = 0
            else :
                self.num_neg_pair += 1
                self.num_cons_neg_pair += 1
                if (self.last_profit is not None and self.last_profit >= 0):
                    self.num_cons_pos_pair = 0
            self.gross_profit += cur_profit
            self.net_profit += cur_profit
            self.last_profit = cur_profit

        self.num_tx += 1
        self.net_profit -= cur_price * (self.fee_rate + self.slippage)

        return ("num_tx: %s, cur_profit: %s, gross_profit: %s, net_profit: %s \n"
                "num_pos_pair: %s, num_neg_pair: %s \n"
                "num_cons_pos_tx: %s num_cons_neg_tx: %s"
               %(self.num_tx, cur_profit, self.gross_profit, self.net_profit,
                 self.num_pos_pair, self.num_neg_pair,
                 self.num_cons_pos_pair, self.num_cons_neg_pair))

    def send_to_slack(self, msg):
        """
        send the message to slack channel
        :param msg:
        :return:
        """
        slack_data = {'text': msg}

        response = requests.post(
            self.webhook_url, data=json.dumps(slack_data),
            headers={'Content-Type': 'application/json'}
        )
        if response.status_code != 200:
            raise ValueError(
                'Request to slack returned an error %s, the response is:\n%s'
                % (response.status_code, response.text)
            )

    def main(self):
        try:
            self.process_message()
        except Exception as ex:
            logging.exception(ex)
            pass

    def run(self):
        print("Starting " + self.name)
        self.main()
        print("Exiting " + self.name)