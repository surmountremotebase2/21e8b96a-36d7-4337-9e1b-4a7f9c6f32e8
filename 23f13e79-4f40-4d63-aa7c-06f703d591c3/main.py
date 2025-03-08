from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import MACD, EMA
from surmount.logging import log
import numpy as np
import pandas as pd

class TradingStrategy(Strategy):
    def __init__(self):
        self.tickers = ["GLD"]
        self.entry_days_count = 0
        self.bullish_days_count = 0

    @property
    def assets(self):
        return self.tickers

    @property
    def interval(self):
        return "1day"

    def WMA(self, prices, period):
       Weighted Moving Average approximated for Hull Moving Average calculation."""
        weights_array = np.arange(1, period + 1)
        return np.dot(prices[-period:], weights_array) / weights_array.sum()

    def run(self, data):
        d = data["ohlcv"]  # Accessing the ohlcv data
        gld_close = np.array([i["GLD"]["close"] for i in d])
        gld_macd = MACD("GLD", d, fast=12, slow=26)["MACD"]  # Getting the MACD line values

        if len(gld_close) < 30:
            # Check if there's enough data
            return TargetAllocation({"GLD": 0})

        # Calculate MACD Histogram
        macd_signal = MACD("GLD", d, fast=12, slow=26, signal=9)["signal"]
        macd_histogram = np.array(gld_macd) - np.array(macd_signal)

        # Hull Moving Average Calculation approximation
        half_length_wma = self.WMA(gld_close, 15 // 2)
        full_length_wma = self.WMA(gld_close, 15)
        hma = self.WMA(2 * half_length_wma - full_length_wma, int(np.sqrt(15)))

        # Conditions
        macd_condition = gld_macd[-1] > 0
        histogram_up_today = macd_histogram[-1] > macd_histogram[-2]
        histogram_down_yesterday = macd_histogram[-2] < macd_histogram[-3]
        hma_upwards = hma > self.WMA(gld_close[:-1], 15)

        entry_condition = macd_condition and histogram_up_today and histogram_down_yesterday and hma_upwards
        exit_condition = self.bullish_days_count >= 3 or self.entry_days_count >= 10

        if entry_condition:
            self.entry_days_count = 1  # Reset the counter on new entry
            self.bullish_days_count = 1 if gld_close[-1] > gld_close[-2] else 0
            log("Entering GLD")
            return TargetAllocation({"GLD": 1})
        elif exit_condition:
            self.entry_days_count = 0
            self.bullish_days_count = 0
            log("Exiting GLD")
            return TargetAllocation({"GLD": 0})
        elif self.entry_days_count > 0:
            # Increment days count and check stop loss condition
            self.entry_days_count += 1
            
            is_bullish_day = gld_close[-1] > gld_close[-2]
            self.bullish_days_count = self.bullish_days_count + 1 if is_bullish_day else 0
            
            # Stop loss check: current price is less than 95% of entry price (for simplicity, last close is considered as entry)
            if gld_close[-1] < gld_close[-self.entry_days_count] * 0.95:
                log("Stop Loss triggered")
                return TargetAllocation({"GLD": 0})
            else:
                return TargetAllocation({"GLD": 1})
            
        else:
            return TargetAllocation({"GLD": 0})