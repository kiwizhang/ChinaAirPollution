import json
import logging
import requests
import time
import threading
from datastore import datastore
from binance.client import Client
from binance.websockets import BinanceSocketManager
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from random import randint

LOG_FILENAME = 'OrderbookSource.log'
timeHandler = TimedRotatingFileHandler(LOG_FILENAME, when="midnight", interval=1)
logging.basicConfig(level=logging.DEBUG, handlers=[timeHandler])
API_KEY = ""
API_SECRET = ""

class OrderbookSource(threading.Thread):

    def __init__(self, threadID, name):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.asks = []
        self.bids = []
        self.combined = []
        self.cur_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.datalist = []
        self.data_lag = 5
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

    def run(self):
        print ("Starting " + self.name)
        self.process_message(self.name, self.counter, 5)
        print ("Exiting " + self.name)
    
    def process_btc_usdt(self, msg):
        self.combined = []
        self.asks = []
        self.bids = []
        for list in msg['data']['asks']:
            for i in range(0, 2):
                self.asks.append(list[i])
        for list in msg['data']['bids']:
            for i in range(0, 2):
                self.bids.append(list[i])
        self.combined = self.combined + self.asks + self.bids
        self.lowestAsk = self.asks[0]
        self.highestBid = self.bids[0]
        self.asks = []
        self.bids = []
        self.btc_usdt_flag = True
        self.eth_btc_flag = False

    def process_eth_usdt(self, msg):
        for list in msg['data']['asks']:
            for i in range(0, 2):
                self.asks.append(list[i])

        for list in msg['data']['bids']:
            for i in range(0, 2):
                self.bids.append(list[i])
        self.combined = self.combined + self.asks + self.bids
        self.asks = []
        self.bids = []
        self.eth_usdt_flag = True
        self.btc_usdt_flag = False
    
    def process_eth_btc(self, msg):
        for list in msg['data']['asks']:
            for i in range(0, 2):
                self.asks.append(list[i])

        for list in msg['data']['bids']:
            for i in range(0, 2):
                self.bids.append(list[i])
        self.combined = self.combined + self.asks + self.bids
        self.asks = []
        self.bids = []
        self.eth_btc_flag = True
        self.eth_usdt_flag = False

    def get_rest(self):
        print("resting...")
        global bm
        global filePath
        logging.error(msg)
        bm.stop_socket(conn_key)
        time.sleep(int(5))
        bm.start()
        print("binance manager restarted")

    def process_message(self, msg):
        print(msg)
        if 'e' in msg and msg['e'] == 'error':
            self.get_rest()
        if msg['stream'].startswith('btcusdt') and self.eth_btc_flag:
            self.process_btc_usdt(msg)
        elif msg['stream'].startswith('ethusdt') and self.btc_usdt_flag:
            self.process_eth_usdt(msg)
        elif msg['stream'].startswith('ethbtc') and self.eth_usdt_flag:
            self.process_eth_btc(msg)
        if len(self.combined) >= 240:
            self.post_cleaning()
            
    def post_cleaning(self):
        self.cur_time = datetime.now().strftime('%Y-%m-%d-%H:%M:%S')
        line = self.cur_time + ',' + ','.join(self.combined)
        words = line[0:len(line) - 2].split(",")
        self.write_flag = True
        line = self.cur_time + ',' + ','.join(self.combined)
        words = line[0:len(line) - 2].split(",")
        if (float(words[81]) < 1):
            if (float(words[161]) < 1):
                self.write_flag = False
            else:
                temp = words[81:161];
                words[81:160] = words[161: len(words)]
                words[161: len(words)] = temp
        if (len(words) > 241):
            words = words[0:241]
        if (self.write_flag):
            if (len(self.datalist) > self.data_lag):
                try:
                    signal = self.get_signal(self.datalist)
                    print("orderbook source running...." + self.cur_time)
                    # print(self.datalist)
                    # logging.debug((str)(self.cur_time) + " signal: " + signal)
                    # self.trigger_bot(signal)
                except Exception as ex:
                    logging.error(ex)
                    pass
                self.datalist.pop(0)
            self.datalist.append(words[1:])
            datastore.set_orderbook_data(self.datalist)
            logging.debug("updated orderbook data   ... " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            self.write_flag = True
        self.combined = []
        self.ask = []
        self.bids = []

    def get_signal(self, datalist):
        """
        Apply the algorithm into the data, and output the signal
        :param datalist: the orderbook data in memory
        :return: the signal: -1, 0 or 1
        """
        from algos import random_generator
        algo = random_generator.random_generator()
        return algo.main(datalist)

    def trigger_bot(self, signal):
        """
        Send the signal to the bot and trigger the action
        :param signal: sell, buy or hold
        :return:
        """
        if (signal == "hold"):
            return
        self.cur_time = datetime.now().strftime('%Y-%m-%d-%H:%M:%S')
        uuid = str(int(time.time()))
        cur_price = ((float)(self.lowestAsk) + (float)(self.highestBid))/2

        if (signal == "buy"):
            self.prev_bought_price = cur_price

        trade_info = self.cur_time + "," + uuid + "," + signal + "," + str(cur_price) + "," + str(self.lowestAsk) + "," + str(self.highestBid)
        logging.info(trade_info)
        print(trade_info)
        trade_stats = self.generate_stats(signal, cur_price)
        logging.info(trade_stats)
        print(trade_stats)
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
            client = Client(API_KEY, API_SECRET)
            bm = BinanceSocketManager(client)
            conn_key = bm.start_multiplex_socket(['btcusdt@depth20', 'ethusdt@depth20', 'ethbtc@depth20'],
                                                self.process_message)
            bm.start()
        except Exception as ex:
            logging.exception(ex)
            pass


    def run(self):
        print("Starting " + self.name)
        self.main()


