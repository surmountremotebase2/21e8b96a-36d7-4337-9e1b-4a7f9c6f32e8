from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import MACD, RSI
from surmount.logging import log
from surmount.data import Asset
import numpy as np

class TradingStrategy(Strategy):
    def __init__(self):
        # Define the tickers we will use in our strategy
        self.tickers = ["SPY", "SHV", "XLU", "XLI"]
        self.data_list = [Asset(ticker) for ticker in self.tickers]

    @property
    def interval(self):
        # Using '1week' to get weekly data as MACD and RSI are based on weeks
        return "1week"

    @property
    def assets(self):
        return self.tickers

    @property
    def data(self):
        return self.data_list

    def run(self, data):
        allocation_dict = {"SPY": 0, "SHV": 0}
        ohlcv_data = data["ohlcv"]
        
        # Calculate MACD with a 10 week period
        macd_signal = MACD("SPY", ohlcv_data, fast=12, slow=26)["signal"]  # Traditional MACD periods
        # Calculate RSI with a 5 week period
        rsi_values = RSI("SPY", ohlcv_data, length=5)

        # Check if we have at least 10 weeks of data to ensure MACD calculation is possible
        if len(macd_signal) >= 10 and len(rsi_values) >= 5:
            # Determine if SPY's latest MACD signal is positive and its RSI is above 30
            if macd_signal[-1] > 0 and rsi_values[-1] > 30:
                allocation_dict["SPY"] = 1  # Buy SPY
            else:
                # Calculate 45 days (~9 weeks) percent change for XLU and XLI
                xlu_percent_change = (ohlcv_data[-1]["XLU"]["close"] - ohlcv_data[-9]["XLU"]["close"]) / ohlcv_data[-9]["XLU"]["close"]
                xli_percent_change = (ohlcv_data[-1]["XLI"]["close"] - ohlcv_data[-9]["XLI"]["close"]) / ohlcv_data[-9]["XLI"]["close"]
                
                # If MACD signal turned negative and XLU's percent change over the last 45 days is greater than XLI's,
                if macd_signal[-1] < 0 and xlu_percent_change > xli_percent_change:
                    allocation_dict["SHV"] = 1  # Buy SHV as a safer investment

        return TargetAllocation(allocation_dict)