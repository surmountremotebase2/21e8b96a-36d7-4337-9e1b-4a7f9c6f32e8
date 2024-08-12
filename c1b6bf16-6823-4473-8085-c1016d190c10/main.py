from surmount.base_class import Strategy, TargetAllocation
from surmount.data import OHLCV
from datetime import datetime
import pandas as pd

class TradingStrategy(Strategy):
    def __init__(self):
        self.asset_tmv = "TMV"
        self.asset_tlt = "TLT"
        self.data_list = [OHLCV(self.asset_tmv), OHLCV(self.asset_tlt)]

    @property
    def interval(self):
        return "1day"

    @property
    def assets(self):
        return [self.asset_tmv, self.asset_tlt]

    @property
    def data(self):
        return self.data_list

    def run(self, data):
        ohlcv_tmv = data['ohlcv'][self.asset_tmv]
        ohlcv_tlt = data['ohlcv'][self.asset_tlt]
        
        current_date = datetime.now().date()
        month_start = current_date.replace(day=1)
        month_end = (month_start + pd.offsets.MonthEnd(1)).date()
        
        last_trading_day_tmv = ohlcv_tmv.index[-1].date()
        last_trading_day_tlt = ohlcv_tlt.index[-1].date()

        allocation = {self.asset_tmv: 0, self.asset_tlt: 0}
        
        # Determine if it's time to trade TMV or TLT based on the calendar day
        if current_date == month_end:
            allocation[self.asset_tmv] = 1  # Buy TMV at month's end
        elif current_date.day == 7 and last_trading_day_tmv >= current_date:
            allocation[self.asset_tmv] = 0  # Sell TMV at the close of the new month's seventh day
        elif current_date.day == 8 and last_trading_day_tlt >= current_date:
            allocation[self.asset_tlt] = 1  # Buy TLT on the eighth day of the new month
        
        return TargetAllocation(allocation)