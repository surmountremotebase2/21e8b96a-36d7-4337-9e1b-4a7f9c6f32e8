
from surmount.base_class import Strategy, TargetAllocation
from surmount.data import OHLCV
from datetime import datetime
import pandas as pd

class TradingStrategy(Strategy):
    def __init__(self):
        self.ShortBond = "TMV"
        self.LongBond = "TLT"


    @property
    def interval(self):
        return "1day"

    @property
    def assets(self):
        return [self.LongBond, self.ShortBond]


    def run(self, data):

        tlt_data = [entry[self.LongBond]['close'] for entry in data['ohlcv'] if self.LongBond in entry]
        tlt_dates = [entry[self.LongBond]['date'] for entry in data['ohlcv'] if self.LongBond in entry]
        tmv_data = [entry[self.ShortBond]['close'] for entry in data['ohlcv'] if self.ShortBond in entry]
        tmv_dates = [entry[self.ShortBond]['date'] for entry in data['ohlcv'] if self.ShortBond in entry]
        
        tlt_data = pd.DataFrame(tlt_data, columns=['close'])
        #tlt_data['returns'] = 100 * tlt_data.close.pct_change().dropna()
        
        today_date = tlt_dates.iloc[-1]
        month_start = today_date.replace(day=1)
        month_end = (month_start + pd.offsets.MonthEnd(1)).date()
        
        last_trading_day_tmv = tmv_dates.iloc[-1]
        last_trading_day_tlt = tlt_dates.iloc[-1]

        allocation = {self.LongBond: 0, self.ShortBond: 0}
        
        # Determine if it's time to trade TMV or TLT based on the calendar day
        if today_date == month_end:
            allocation[self.ShortBond] = 1  # Buy TMV at month's end
        elif today_date.day == 7 and last_trading_day_tmv >= today_date:
            allocation[self.ShortBond] = 0  # Sell TMV at the close of the new month's seventh day
        elif today_date.day == 8 and last_trading_day_tlt >= today_date:
            allocation[self.LongBond] = 1  # Buy TLT on the eighth day of the new month
        
        return TargetAllocation(allocation)
