from surmount.base_class import Strategy, TargetAllocation, backtest
from surmount.logging import log
import pandas as pd
import numpy as np
from datetime import date, time, datetime, timedelta

class TradingStrategy(Strategy):
    def __init__(self):
        self.tickers = ["QQQ", "TQQQ"]

    @property
    def assets(self):
        return self.tickers

    @property
    def interval(self):
        # Using daily data as the strategy specifies actions based on daily close prices
        return "1day"

    def run(self, data):
        d = data["ohlcv"] # Getting OHLCV data for QQQ
        allocation = 0
        
        if len(d) >= 2:  # We need at least 2 days of data to proceed
            closes = np.array([item["QQQ"]["close"] for item in d[-3:]])  # Last 3 days close prices [for current day and 2 days back]
            highs = np.array([item["QQQ"]["high"] for item in d[-3:]])  # Last 3 days high prices
            lows = np.array([item["QQQ"]["low"] for item in d[-3:]])  # Last 3 days low prices

            # Williams %R calculation for the previous day
            highest_high = np.max(highs[:-1])
            lowest_low = np.min(lows[:-1])
            close_yesterday = closes[-2]
            williams_r_yesterday = ((highest_high - close_yesterday) / (highest_high - lowest_low)) * -100

            # Williams %R calculation for today
            highest_high_today = np.max(highs)
            lowest_low_today = np.min(lows)
            close_today = closes[-1]
            williams_r_today = ((highest_high_today - close_today) / (highest_high_today - lowest_low_today)) * -100

            #log(f"Williams %R Yesterday: {williams_r_yesterday}, Williams %R Today: {williams_r_today}")

            # Buy signal based on Williams %R and conditions for selling
            if williams_r_yesterday < -90:
                allocation = 1  # Entry condition met, going long
            if close_today > highs[-2] or williams_r_today > -30:  # Exit conditions
                allocation = 0  # Sell signal
            
        return TargetAllocation({"TQQQ": allocation})