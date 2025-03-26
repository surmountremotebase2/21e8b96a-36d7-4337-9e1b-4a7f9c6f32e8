from surmount.base_class import Strategy, TargetAllocation
from surmount.data import CivilianUnemployment
from surmount.logging import log


class TradingStrategy(Strategy):
    def __init__(self):
        self.tickers = ["AAPL"]
        self.data_list = [CivilianUnemployment()]

    @property
    def interval(self):
        # Use daily data as economic indicators do not update more frequently
        return "1day"

    @property
    def assets(self):
        # We are only trading AAPL based on economic indicators
        return self.tickers

    @property
    def data(self):
        return self.data_list

    def run(self, data):
        allocation_dict = {"AAPL": 0} 
        unemployment_data = data[("civilian_unemployment",)]

        if  len(unemployment_data) > 1:
            latest_unemployment_change = unemployment_data[-1]["value"] - unemployment_data[-2]["value"]

            if latest_unemployment_change <= 0:
                allocation_dict["AAPL"] = 1  # Full allocation to AAPL
            elif latest_unemployment_change > 0:
                allocation_dict["AAPL"] = 0  # No position in AAPL
                
            log(f"Latest Unemployment Change: {latest_unemployment_change}")

        return TargetAllocation(allocation_dict)