from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import SMA
from surmount.logging import log

class TradingStrategy(Strategy):
    def __init__(self):
        self.ticker = "QQQ"
    
    @property
    def assets(self):
        return [self.ticker]

    @property
    def interval(self):
        return "1day"
    
    def run(self, data):
        allocation_dict = {self.ticker: 0}  # Default to no allocation
        ohlcv_data = data["ohlcv"]
        if len(ohlcv_data) < 25:
            log("Not enough data to evaluate 25-day high.")
            return TargetAllocation(allocation_dict)
        
        # Extract closing prices
        closes = [day[self.ticker]["close"] for day in ohlcv_data]
        # Calculate the 25-day high
        high_25_day = max(closes[-27:-2])
        
        # Current close price
        current_close = closes[-1]

        # Check if current close is above 25-day high
        if current_close > high_25_day:
            log("Current close is above the 25-day high. Buying QQQ.")
            allocation_dict[self.ticker] = 1  # Buy (allocate 100% to QQQ)
        elif current_close < high_25_day:
            log("Current close is below the 25-day high. Selling QQQ.")
            allocation_dict[self.ticker] = 0  # Sell (close position)

        return TargetAllocation(allocation_dict)