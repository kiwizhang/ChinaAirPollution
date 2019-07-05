from datastore import datastore
import threading
import time

class SampleAlgo(threading.Thread):

    def __init__(self, threadID, name):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name

    def generate_signal(self, kline_data, orderbook_data):
        #apply the algorithm to the data, then return signal(-1, 0 or 1)
        #signal = algo(klinedata)
        # print(kline_data)
        # print(orderbook_data)
        return 1

    def main(self):
        while True:
            self.generate_signal(datastore.get_kline_data(), datastore.get_orderbook_data())
            time.sleep(3)


    def run(self):
        print("Starting " + self.name)
        self.main()
        print("Exiting " + self.name)




