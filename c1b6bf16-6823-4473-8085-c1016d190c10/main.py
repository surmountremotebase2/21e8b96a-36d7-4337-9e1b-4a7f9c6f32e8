from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import RSI, EMA, SMA
from surmount.logging import log
import pandas as pd
import numpy as np
from datetime import datetime

class TradingStrategy(Strategy):
    def __init__(self):
        self.ShortBond = "TMV"
        self.LongBond = "TLT"
        self.tickers = [self.LongBond, self.ShortBond]

    @property
    def assets(self):
        # Defines the asset to trade
        return self.tickers

    @property
    def interval(self):
        # Sets the strategy to run on daily data
        return "1day"


    def run(self, data):

        tlt_data = [entry[self.LongBond]['close'] for entry in data['ohlcv'] if self.LongBond in entry]
        tlt_dates = [entry[self.LongBond]['date'] for entry in data['ohlcv'] if self.LongBond in entry]
        tmv_data = [entry[self.ShortBond]['close'] for entry in data['ohlcv'] if self.ShortBond in entry]
        tmv_dates = [entry[self.ShortBond]['date'] for entry in data['ohlcv'] if self.ShortBond in entry]
        
        tlt_data = pd.DataFrame(tlt_data, columns=['close'])
        #tlt_data['returns'] = 100 * tlt_data.close.pct_change().dropna()
        
        today_date = tlt_dates[-1].split(" ")[0]
        today_date = datetime.strptime(today_date, "%Y-%m-%d")
        log(f"{tlt_dates[-1]}")
        log(f"{today_date}")
        
        month_start = today_date.replace(day=1)
        month_end = (month_start + pd.offsets.MonthEnd(1)).date()
        
        last_trading_day_tmv = tmv_dates[-1]
        last_trading_day_tlt = tlt_dates[-1]

        allocation = {self.LongBond: 0, self.ShortBond: 0}
        
        # Determine if it's time to trade TMV or TLT based on the calendar day
        if today_date == month_end:
            allocation[self.ShortBond] = 1  # Buy TMV at month's end
        elif today_date.day == 7 and last_trading_day_tmv >= today_date:
            allocation[self.ShortBond] = 0  # Sell TMV at the close of the new month's seventh day
        elif today_date.day == 8 and last_trading_day_tlt >= today_date:
            allocation[self.LongBond] = 1  # Buy TLT on the eighth day of the new month
        
        return TargetAllocation(allocation)
