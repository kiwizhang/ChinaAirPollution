#!/usr/bin/python3

# this script will be deleted later
# we are using it only to test if we can get data from both source
# after testing, we will move them into source folder


from sources.KlineSource import KlineSource
from sources.OrderbookSource import OrderbookSource
from algos.sample_algo import SampleAlgo
import threading
import time

# exitFlag = 0
#
# class myThread (threading.Thread):
#    def __init__(self, threadID, name, counter):
#       threading.Thread.__init__(self)
#       self.threadID = threadID
#       self.name = name
#       self.counter = counter
#    def run(self):
#       print ("Starting " + self.name)
#       print_time(self.name, self.counter, 5)
#       print ("Exiting " + self.name)
#
# def print_time(threadName, delay, counter):
#    while counter:
#       if exitFlag:
#          threadName.exit()
#       time.sleep(delay)
#       print ("%s: %s" % (threadName, time.ctime(time.time())))
#       counter -= 1


# Create new threads
kline_thread = KlineSource(1, "kline")
orderbook_thread = OrderbookSource(2, "orderbook")
algo_thread = SampleAlgo(3, "algo")

# Start new Threads
kline_thread.start()
orderbook_thread.start()
algo_thread.start()
kline_thread.join()
orderbook_thread.join()
algo_thread.join()
# print ("Exiting Main Thread")