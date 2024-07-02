from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import RSI, SMA, BB
from surmount.logging import log

class TradingStrategy(Strategy):

    def __init__(self):
        self.tickers = ["USO"]

    @property
    def interval(self):
        return "1day"

    @property
    def assets(self):
        return self.tickers

    @property
    def data(self):
        return []

    def run(self, data):
        allocation_dict = {"USO": 0}  # Default to no allocation

        # Calculate the 200-day Bollinger Bands with 1.2 standard deviations
        bb = BB("USO", data["ohlcv"], 200, 1.2)
        # Calculate the 50-day RSI
        rsi = RSI("USO", data["ohlcv"], 50)
        # Calculate the 30-day and 15-day SMA
        sma30 = SMA("USO", data["ohlcv"], 30)
        sma15 = SMA("USO", data["ohlcv"], 15)
        
        if not bb or not rsi or not sma30 or not sma15:
            return TargetAllocation(allocation_dict)  # Return no allocation if any calculation failed

        current_close = data["ohlcv"][-1]["USO"]['close']
        
        # Check if current close price is above the upper Bollinger band, RSI > 50, and close > 30-day SMA
        if current_close > bb['upper'][-1] and rsi[-1] > 50 and current§_close > sma30[-1]:
            allocation_dict["USO"] = 1  # Full allocation to USO
        # Check if the position should be closed - close is below the 15-day SMA or RSI < 50
        elif current_close < sma15[-1] or rsi[-1] < 50:
            allocation_dict["USO"] = 0  # Close position
        
        return TargetAllocation(allocation_dict)