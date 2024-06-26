from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import SMA
from surmount.logging import log

class TradingStrategy(Strategy):
    def __init__(self):
        self.ticker = "SPY"
        self.TEC = "TECL"
    
    @property
    def assets(self):
        return [self.ticker, self.TEC]

    @property
    def interval(self):
        return "1day"
    
    def run(self, data):
        allocation_dict = {self.TEC: 0}  # Default to no allocation
        ohlcv_data = data["ohlcv"]
        if len(ohlcv_data) < 101:
            log("Not enough data to evaluate 25-day high.")
            return TargetAllocation(allocation_dict)
        
        # Extract closing prices
        closes = [day[self.ticker]["close"] for day in ohlcv_data]
        # Calculate the 25-day high
        high_25_day = max(closes[-1:-100])
        low_25_day = min(closes[-1:-100])
        
        # Current close price
        current_close = closes[-1]

        # Check if current close is above 25-day high
        if current_close >= high_25_day:
            #log("Current close is above the 25-day high. Buying QQQ.")
            allocation_dict[self.TEC] = 1  # Buy (allocate 100% to QQQ)
        elif current_close <= low_25_day:
            #log("Current close is below the 25-day high. Selling QQQ.")
            allocation_dict[self.TEC] = 0  # Sell (close position)

        return TargetAllocation(allocation_dict)