from surmount.base_class import Strategy, TargetAllocation
from surmount.logging import log

class TradingStrategy(Strategy):

    def __init__(self):
        self.ticker = "AAPL"
        self.amount = 100  # Dollar amount to invest at each interval
        self.investment_interval = 30  # Number of days between investments
        self.count = 0
        self.target_allocation = 0

    @property
    def interval(self):
        return "1day"

    @property
    def assets(self):
        return [self.ticker]

    def run(self, data):
        self.count += 1
        if self.count % self.investment_interval == 1 and len(data["ohlcv"])>0:
            current_price = data["ohlcv"][-1][self.ticker]["close"]
            self.target_allocation += self.amount / current_price
            return TargetAllocation({self.ticker: min(1, self.target_allocation)})
        return None