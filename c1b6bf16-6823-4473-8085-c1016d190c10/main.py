from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import RSI, EMA, SMA
from surmount.logging import log
import pandas as pd
import numpy as np
from datetime import datetime

class TradingStrategy(Strategy):
    def __init__(self):
        self.ShortBond = "TMV"
        self.LongBond = "TMF"
        self.Equity = "SPY"
        self.Gold = "GLD"
        
        self.mrkt = "TLT"
        self.tickers = [self.LongBond, self.ShortBond, self.Equity, self.mrkt]
        self.count = 5

    @property
    def assets(self):
        # Defines the asset to trade
        return self.tickers

    @property
    def interval(self):
        # Sets the strategy to run on daily data
        return "1day"

    def realized_volatility_daily(self, series_log_return):
        """
        Get the daily realized volatility which is calculated as the square root
        of sum of squares of log returns within a specific window interval 
        """
        n = len(series_log_return)
        vola =  np.sqrt(np.sum(series_log_return**2)/(n - 1))
        return vola


    def run(self, data):
        allocation_dict = {ticker: 0 for ticker in self.tickers}

        if len(data) > 0:
            today = datetime.strptime(str(next(iter(data['ohlcv'][-1].values()))['date']), '%Y-%m-%d %H:%M:%S')
            yesterday = datetime.strptime(str(next(iter(data['ohlcv'][-2].values()))['date']), '%Y-%m-%d %H:%M:%S')
            self.count -= 1
            
            mrktData = [entry[self.mrkt]['close'] for entry in data['ohlcv'] if self.mrkt in entry]
            mrktData = pd.DataFrame(mrktData, columns=['close'])
            mrktData['log_returns'] = np.log(mrktData.close/mrktData.close.shift(1))
            mrktData = mrktData.fillna(0)
            INTERVAL_WINDOW = 60
            n_future = 20

            tlt_data = [entry[self.LongBond]['close'] for entry in data['ohlcv'] if self.LongBond in entry]
            tlt_dates = [entry[self.LongBond]['date'] for entry in data['ohlcv'] if self.LongBond in entry]
            tmv_data = [entry[self.ShortBond]['close'] for entry in data['ohlcv'] if self.ShortBond in entry]
            tmv_dates = [entry[self.ShortBond]['date'] for entry in data['ohlcv'] if self.ShortBond in entry]
            
            tlt_data = pd.DataFrame(tlt_data, columns=['close'])
            
            today_date = tlt_dates[-1].split(" ")[0]
            today_date = datetime.strptime(today_date, "%Y-%m-%d")
            
            month_start = today_date.replace(day=1)
            month_end = (month_start + pd.offsets.MonthEnd(1)).date()
            
            last_trading_day_tmv = tmv_dates[-1].split(" ")[0]
            last_trading_day_tmv = datetime.strptime(last_trading_day_tmv, "%Y-%m-%d")
            last_trading_day_tlt = tlt_dates[-1].split(" ")[0]
            last_trading_day_tlt = datetime.strptime(last_trading_day_tlt, "%Y-%m-%d")
            mrktData['vol_current'] = mrktData.log_returns.rolling(window=INTERVAL_WINDOW).apply(self.realized_volatility_daily)
            mrktData['vol_current'] = mrktData['vol_current'].bfill()
            # GET FORWARD LOOKING REALIZED VOLATILITY 
            mrktData['vol_future'] = mrktData.log_returns.shift(n_future).fillna(0).rolling(window=INTERVAL_WINDOW).apply(self.realized_volatility_daily)
            mrktData['vol_future'] = mrktData['vol_future'].bfill()

            mrktEMA = EMA(self.mrkt, data["ohlcv"], length=200)
            mrktClose = mrktData.close.iloc[-1]

            if (mrktData['vol_current'].iloc[-1] > mrktData['vol_future'].iloc[-1]):
                self.count = 5

                if today_date == month_end:
                    allocation_dict[self.ShortBond] = 1  # Buy TMV at month's end
                    allocation_dict[self.LongBond] = 0
                    allocation_dict[self.Equity] = 0
                elif today_date.day == 7 and last_trading_day_tmv >= today_date:
                    allocation_dict[self.ShortBond] = 0  # Sell TMV at the close of the new month's seventh day
                    allocation_dict[self.LongBond] = 0
                    allocation_dict[self.Equity] = 0
                elif today_date.day == 8 and last_trading_day_tlt >= today_date:
                    allocation_dict[self.LongBond] = 0  # Buy TLT on the eighth day of the new month
                    allocation_dict[self.ShortBond] = 0
                    allocation_dict[self.Equity] = 1
            
            elif self.count < 1 and mrktClose > mrktEMA[-2]:
                if today_date == month_end:
                    allocation_dict[self.ShortBond] = 1  # Buy TMV at month's end
                    allocation_dict[self.LongBond] = 0
                    allocation_dict[self.Equity] = 0
                elif today_date.day == 7 and last_trading_day_tmv >= today_date:
                    allocation_dict[self.ShortBond] = 0  # Sell TMV at the close of the new month's seventh day
                    allocation_dict[self.LongBond] = 0
                    allocation_dict[self.Equity] = 0
                elif today_date.day == 8 and last_trading_day_tlt >= today_date:
                    allocation_dict[self.LongBond] = 1  # Buy TLT on the eighth day of the new month
                    allocation_dict[self.ShortBond] = 0
                    allocation_dict[self.Equity] = 0
            
            else:
                if today_date == month_end:
                    allocation_dict[self.ShortBond] = 1  # Buy TMV at month's end
                    allocation_dict[self.LongBond] = 0
                    allocation_dict[self.Equity] = 0
                elif today_date.day == 7 and last_trading_day_tmv >= today_date:
                    allocation_dict[self.ShortBond] = 0  # Sell TMV at the close of the new month's seventh day
                    allocation_dict[self.LongBond] = 0
                    allocation_dict[self.Equity] = 0
                elif today_date.day == 8 and last_trading_day_tlt >= today_date:
                    allocation_dict[self.LongBond] = 1  # Buy TLT on the eighth day of the new month
                    allocation_dict[self.ShortBond] = 0
                    allocation_dict[self.Equity] = 0

            
            return TargetAllocation(allocation_dict)

        else:
            return TargetAllocation(allocation_dict)
