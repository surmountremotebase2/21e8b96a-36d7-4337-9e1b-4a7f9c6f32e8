from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import RSI, EMA, SMA
from surmount.logging import log
import pandas as pd
import numpy as np

class TradingStrategy(Strategy):
    def __init__(self):
        # Only trading with "USO" ETF
        self.ticker = ["SPY", "QQQ", "BIL"]
        self.mrkt = "QQQ"
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
        mrktData = [entry[self.mrkt]['close'] for entry in data['ohlcv'] if self.mrkt in entry]
        #spy_dates = [entry['QQQ']['date'] for entry in data['ohlcv'] if 'QQQ' in entry]
        mrktData = pd.DataFrame(mrktData, columns=['close'])
        #spy_data['returns'] = 100 * spy_data.close.pct_change().dropna()
        # CALCULATE LOG RETURNS BASED ON ABOVE FORMULA
        mrktData['log_returns'] = np.log(mrktData.close/spy_data.close.shift(1))
        mrktData = mrktData.fillna(0)
        INTERVAL_WINDOW = 60
        n_future = 20


        if len(spy_data) > n_future:
            # GET BACKWARD LOOKING REALIZED VOLATILITY
            mrktData['vol_current'] = spy_data.log_returns.rolling(window=INTERVAL_WINDOW).apply(self.realized_volatility_daily)
            mrktData['vol_current'] = spy_data['vol_current'].bfill()
            # GET FORWARD LOOKING REALIZED VOLATILITY 
            mrktData['vol_future'] = mrktData.log_returns.shift(n_future).fillna(0).rolling(window=INTERVAL_WINDOW).apply(self.realized_volatility_daily)
            mrktData['vol_future'] = mrktData['vol_future'].bfill()
            volaT = np.percentile(mrktData['vol_current'], 55)
            volaH = np.percentile(mrktData['vol_current'], 80)
            mrktEMA = EMA(self.mrkt, data["ohlcv"], length=100)
            mrktClose = mrktData.close.iloc[-1]

            if (spy_data['vol_current'].iloc[-1] > spy_data['vol_future'].iloc[-1] and spy_data['vol_current'].iloc[-1] > volaT):

                allocation[self.RiskOn] = 0
                allocation[self.RiskOff] = 1.0
                if spy_data['vol_current'].iloc[-1] > volaH:
                    self.count = 10
                else:
                    self.count = 5
            
            elif self.count < 1 and mrktClose > mrktEMA:
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
