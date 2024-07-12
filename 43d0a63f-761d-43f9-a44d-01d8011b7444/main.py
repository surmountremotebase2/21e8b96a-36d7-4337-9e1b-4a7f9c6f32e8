from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import RSI, EMA, SMA
from surmount.logging import log

class TradingStrategy(Strategy):
    def __init__(self):
        # Only trading with "USO" ETF
        self.ticker = "SPY"

    @property
    def assets(self):
        # Defines the asset to trade
        return [self.ticker]

    @property
    def interval(self):
        # Sets the strategy to run on daily data
        return "1day"

    def run(self, data):
        # The trading logic goes here
        uso_allocation = 1.0

        # Return the allocation object with the calculated allocation
        return TargetAllocation({self.ticker: uso_allocation})