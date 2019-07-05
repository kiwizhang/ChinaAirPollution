from constants import *

class Datastore():
    def __init__(self):
        self.data = {KLINE: None,
                     ORDERBOOK: None}

    def get_kline_data(self):
        return self.data[KLINE]

    def get_orderbook_data(self):
        return self.data[ORDERBOOK]

    def set_kline_data(self, updated_data):
        self.data[KLINE] = updated_data

    def set_orderbook_data(self, updated_data):
        self.data[ORDERBOOK] = updated_data

datastore = Datastore()


