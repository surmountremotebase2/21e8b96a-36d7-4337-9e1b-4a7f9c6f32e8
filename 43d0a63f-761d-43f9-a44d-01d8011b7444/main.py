from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import RSI, EMA, SMA
from surmount.logging import log
import pandas as pd
import numpy as np

class TradingStrategy(Strategy):
    def __init__(self):
        # Only trading with "USO" ETF
        self.ticker = ["SPY", "QQQ", "QQQ", "BIL"]
        self.RiskOn = "QQQ"
        self.RiskOff = "BIL"
        self.count = 5

    @property
    def assets(self):
        # Defines the asset to trade
        return self.ticker

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
        allocation = {}
        self.count -= 1
        spy_data = [entry['QQQ']['close'] for entry in data['ohlcv'] if 'QQQ' in entry]
        #spy_dates = [entry['QQQ']['date'] for entry in data['ohlcv'] if 'QQQ' in entry]
        spy_data = pd.DataFrame(spy_data, columns=['close'])
        #spy_data['returns'] = 100 * spy_data.close.pct_change().dropna()
        # CALCULATE LOG RETURNS BASED ON ABOVE FORMULA
        spy_data['log_returns'] = np.log(spy_data.close/spy_data.close.shift(1))
        spy_data = spy_data.fillna(0)
        INTERVAL_WINDOW = 60
        n_future = 20


        if len(spy_data) > n_future:
            # GET BACKWARD LOOKING REALIZED VOLATILITY
            spy_data['vol_current'] = spy_data.log_returns.rolling(window=INTERVAL_WINDOW).apply(self.realized_volatility_daily)
            spy_data['vol_current'] = spy_data['vol_current'].bfill()
            # GET FORWARD LOOKING REALIZED VOLATILITY 
            spy_data['vol_future'] = spy_data.log_returns.shift(n_future).fillna(0).rolling(window=INTERVAL_WINDOW).apply(self.realized_volatility_daily)
            spy_data['vol_future'] = spy_data['vol_future'].bfill()
            volaT = np.percentile(spy_data['vol_current'], 55)
            volaH = np.percentile(spy_data['vol_current'], 80)
            mrktRSI = RSI("QQQ", data['ohlcv'], 10)

            if (spy_data['vol_current'].iloc[-1] > spy_data['vol_future'].iloc[-1] and spy_data['vol_current'].iloc[-1] > volaT and mrktRSI > 50):

                allocation[self.RiskOn] = 0
                allocation[self.RiskOff] = 1.0
                if spy_data['vol_current'].iloc[-1] > volaH:
                    self.count = 20
                else:
                    self.count = 10
            
            elif self.count < 1:
                allocation[self.RiskOn] = 1.0
                allocation[self.RiskOff] = 0
            else:
                allocation[self.RiskOn] = 0
                allocation[self.RiskOff] = 1.0
            
            return TargetAllocation(allocation)
        else:
            allocation[self.RiskOn] = 0
            allocation[self.RiskOff] = 1.0
            return TargetAllocation(allocation)
