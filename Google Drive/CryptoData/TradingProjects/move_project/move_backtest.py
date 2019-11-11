import requests
import json
import move_strategy
from datetime import datetime, timedelta

class BackTest:

    def __init__(self):
        self.total_trades = 0
        self.total_pnl = 0
        self.positive_days = 0
        self.negative_days = 0

    def run(self):
        contracts = self.get_move_contract_names("MOVE-BTC-1109")
        for contract in contracts:
            print("\n\nstats for %s :" % (contract))
            strategy = move_strategy.MoveStrategy(contract)
            data = self.get_move_contract_data(contract)
            datetime_object = datetime.strptime(contract[-4:], '%m%d') - timedelta(days=1)
            date_str = str(datetime_object)[5:10]
            for item in data:
                if date_str in str(item["startTime"]):
                    signal = strategy.run(item["close"], item["startTime"])
            stats = strategy.get_summary()
            self.total_trades += stats[0]
            self.total_pnl += stats[1]
            if stats[1] > 0:
                self.positive_days += 1
            else:
                self.negative_days += 1
        print("-------------------------------------------")
        print("total trades: %s" % self.total_trades)
        print("total pnl: %s" % self.total_pnl)
        print("positive pnl days: %s" % self.positive_days)
        print("negative pnl days: %s" % self.negative_days)
        print("-------------------------------------------")



    def get_move_contract_data(self, contract_name):
        r = requests.get(
            "https://ftx.com/api/futures/" + contract_name + "/mark_candles?resolution=300&limit=100000")
        data = json.loads(r.content)["result"]
        return data

    def get_move_contract_names(self, cur_contract):
        contracts = []
        date_str = cur_contract[-4:]
        for i in range(1, 12):
            datetime_object = datetime.strptime(date_str, '%m%d') - timedelta(days=i)
            contract_name = "BTC-MOVE-" + str(datetime_object)[5:10].replace("-", "")
            contracts.insert(0, contract_name)
        return contracts



if __name__ == "__main__":
    BackTest().run()
