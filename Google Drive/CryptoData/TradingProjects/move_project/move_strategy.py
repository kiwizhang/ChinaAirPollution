import requests
import json
from datetime import datetime, timedelta

class MoveStrategy:

    def __init__(self, contract):
        self.order_price = 0
        self.url = ""
        self.cur_contract = contract
        self.btc_dict = {}
        self.get_btc_data()
        self.fair_value = self.cal_fair_value()
        self.percent_interval = 0.1
        self.max_percent = 0.5
        self.max_level = self.max_percent / self.percent_interval
        self.contract_pnl = 0.0
        self.total_pnl = 0
        self.trades = 0
        self.max_capital = 100
        self.delta = 0
        self.close_percent = 0.2
        self.close_price = None
        self.enter_price = 0
        self.cur_level = 0
        self.last_price = 0
        self.last_time = None

    def run(self, price, time):
        btc_price = self.btc_dict[time]
        target_level = self.get_target_level(price, btc_price)
        price_percent = price / self.btc_dict[time]
        level_diff = target_level - self.cur_level
        self.last_price = price
        self.last_time = time
        if level_diff == 0:
            return "hold", 0
        # print("price %s, percent %s, target level %s, cur level %s" %(price, price_percent, target_level, self.cur_level))
        if self.delta <= 0 and level_diff > 0:
            self.cur_level = target_level
            open_amount = int(level_diff * self.max_capital) if level_diff < self.max_percent else int(self.max_percent * self.max_capital)
            self.enter_price = (self.enter_price * self.delta - price * open_amount) / (self.delta - open_amount)
            self.close_price = (1 + self.cur_level * self.close_percent) * self.fair_value * btc_price
            self.delta -= open_amount
            self.trades += 1
            print("short at %s, move_btc ratio %.4f, amount %s, average enter price %.2f, target close price %.2f" % (price, price_percent, open_amount, self.enter_price, self.close_price))
            return "short", open_amount
        if self.delta < 0 and level_diff < 0:
            if price < self.close_price:
                self.cur_level = target_level
                close_amount = abs(self.delta)
                self.delta = 0
                self.close_price = None
                cur_pnl = (self.enter_price - price) * close_amount / self.enter_price
                self.contract_pnl += cur_pnl
                self.trades += 1
                print("close_short at %s, move_btc ratio %.4f, amount %s, average enter price %.2f, current pnl %.2f" % (price, price_percent, close_amount, self.enter_price, cur_pnl))
                return "close_short", close_amount
            return "hold", 0
        if self.delta >= 0 and level_diff < 0:
            self.cur_level = target_level
            open_amount = abs(int(level_diff * self.max_capital)) if abs(level_diff) < self.max_percent else abs(int(self.max_percent * self.max_capital))
            self.enter_price = (self.enter_price * self.delta + price * open_amount) / (self.delta + open_amount)
            self.close_price = (1 + self.cur_level * self.close_percent) * self.fair_value * btc_price
            self.delta += open_amount
            self.trades += 1
            print("long at %s,  move_btc ratio %.4f, amount %s, average enter price %.2f, target close price %.2f" % (price, price_percent, open_amount, self.enter_price, self.close_price))
            return "long", open_amount
        if self.delta > 0 and level_diff > 0:
            if price > self.close_price:
                self.cur_level = target_level
                close_amount = abs(self.delta)
                self.delta = 0
                cur_pnl = (price - self.enter_price) * close_amount / self.enter_price
                self.contract_pnl += cur_pnl
                self.close_price = None
                self.trades += 1
                print("close_long at %s, move_btc ratio %.4f, amount %s, average enter price %.2f, current pnl %.2f" % (price, price_percent, close_amount, self.enter_price, cur_pnl))
                return "close_long", close_amount
            return "hold", 0
        return "hold", 0


    def get_target_level(self, move_price, btc_price):
        cur_percent = move_price / btc_price
        percent_diff = (cur_percent - self.fair_value) / self.fair_value
        return int(percent_diff / self.percent_interval) * self.percent_interval

    def cal_fair_value(self):
        contracts = self.get_move_contract_names()
        lows = []
        highs = []
        for contract in contracts:
            low, high = self.get_data_for_contract(contract)
            lows.append(low)
            highs.append(high)
        range_low = 0.1 * lows[0] + 0.2 * lows[1] + 0.3 * lows[2] + 0.4*lows[3]
        range_high = 0.1 * highs[0] + 0.2 * highs[1] + 0.3 * highs[2] + 0.4 * highs[3]
        fair_value = (range_low + range_high) / 2
        print("range low: %.4f, range high: %.4f , fair value: %.4f" % (range_low, range_high, fair_value))
        return fair_value

    def get_move_contract_names(self):
        contracts = []
        date_str = self.cur_contract[-4:]
        for i in range(1, 5):
            datetime_object = datetime.strptime(date_str, '%m%d') - timedelta(days=i)
            contract_name = "BTC-MOVE-" + str(datetime_object)[5:10].replace("-", "")
            contracts.insert(0, contract_name)
        print("using data of %s to decide range" %(contracts))
        return contracts

    def get_btc_data(self):
        r = requests.get("https://ftx.com/api/markets/BTC/USD/candles?resolution=300&limit=1000000")
        btc_data = json.loads(r.content)["result"]
        for item in btc_data:
            self.btc_dict[item["startTime"]] = item["close"]


    def get_data_for_contract(self, contract):
        r = requests.get("https://ftx.com/api/futures/" + contract + "/mark_candles?resolution=300&limit=100000")
        move_data = json.loads(r.content)["result"]
        datetime_object = datetime.strptime(contract[-4:], '%m%d') - timedelta(days=1)
        date_str = str(datetime_object)[5:10]
        low_data = []
        high_data = []
        for item in move_data:
            if date_str in str(item["startTime"]):
                low_data.append(item["low"] / self.btc_dict[item["startTime"]])
                high_data.append(item["high"] / self.btc_dict[item["startTime"]])
        return min(low_data), max(high_data)

    def get_summary(self):
        btc_price = self.btc_dict[self.last_time]
        price_percent = self.last_price / btc_price
        cur_pnl = 0
        if self.delta > 0:
            cur_pnl = (self.last_price - self.enter_price) * self.delta / self.enter_price
            print("close_long at %s, move_btc ratio %.4f, amount %s" % (self.last_price, price_percent, self.delta))
            self.trades += 1
        elif self.delta < 0:
            cur_pnl = (self.enter_price - self.last_price) * (-1 * self.delta) / self.enter_price
            print("close_short at %s, move_btc ratio %.4f, amount %s" % (self.last_price, price_percent, self.delta))
            self.trades += 1
        self.delta = 0
        self.contract_pnl += cur_pnl
        self.total_pnl += self.contract_pnl
        print("closing pnl: %.4f" % cur_pnl)
        print("pnl for contract %.4f" % self.contract_pnl)
        print("number of trades %s" % self.trades)
        return self.trades, self.contract_pnl





# if __name__ == "__main__":
#    MoveStrategy().cal_range()
