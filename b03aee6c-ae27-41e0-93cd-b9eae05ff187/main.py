from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import RSI, EMA
from surmount.logging import log

class TradingStrategy(Strategy):
    def __init__(self):
        self.tickers = ["QQQ", "BIL", "TQQQ"]  # Define the assets we are interested in

    @property
    def assets(self):
        return self.tickers  # The Strategy is interested in "QQQ" and "BIL"

    @property
    def interval(self):
        return "1day"  # Data interval to compute indicators

    def run(self, data):
        # Initialize allocation dictionary
        allocation_dict = {"TQQQ": 0, "BIL": 0}
        
        # Calculate 3-day RSI for QQQ
        rsi_values = RSI("QQQ", data["ohlcv"], length=3)
        ema = EMA("QQQ", data["ohlcv"], length=200)
        
        if not rsi_values or len(rsi_values) < 2:
            # Not enough data to calculate RSI or act upon it
            return TargetAllocation(allocation_dict)
        
        # Get previous and latest RSI values
        latest_rsi = rsi_values[-1]
        latest_ema = ema[-1]

        # Access the OHLCV data for QQQ to compare current close with previous high
        data = data["ohlcv"]
        
        # Ensure there is enough data for comparison
        if len(data) >= 2:
            current_close = data[-1]["QQQ"]["close"]
            tecl_close = data[-1]["TQQQ"]["close"]
            previous_high = data[-2]["QQQ"]["high"]
            
            # RSI buy signal check
            if latest_rsi < 26:
                allocation_dict["TQQQ"] = 1.0  # Allocate 100% to QQQ
            # Condition to sell QQQ and buy BIL
            elif current_close > previous_high:
                allocation_dict["BIL"] = 1.0  # Allocate 100% to BIL
            elif latest_rsi < 10:
                allocation_dict["BIL"] = 1.0  # Allocate 100% to BIL
            # If no conditions met, hold current positions
        else:
            # Not enough data for comparing close and high, do nothing
            log("Not enough data for action")
        
        return TargetAllocation(allocation_dict)