from surmount.base_class import Strategy, TargetAllocation, backtest
from surmount.logging import log
from datetime import datetime
import pandas as pd
import numpy as np

class TradingStrategy(Strategy):

    def __init__(self):
        self.tickers = ["NVDA", "GOOGL", "MSFT", "AMZN", "TSLA", "IBM", "INTC", "BIDU", "AMD", "CRM", "NOW", "TWLO", "PATH", "CGNX", "MU", "ASML", "DOCU", "CRWD", "OKTA", "PLTR", "ZS", "FSLY", "SNOW", "DDOG", "SNPS", "CDNS", "ANSS", "ADSK", "NTNX", "APPN", "ANET", "TDC", "PEGA", "VRNS", "AI", "ESTC", "TENB"]
        self.weights = [0.06, 0.06, 0.06, 0.06, 0.06, 0.04, 0.04, 0.04, 0.04, 0.03, 0.03, 0.02, 0.02, 0.02, 0.04, 0.02, 0.03, 0.02, 0.01, 0.01, 0.02, 0.02, 0.03, 0.01, 0.01, 0.01, 0.01, 0.02, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.06]
        self.bench = ["SPY"]
        self.equal_weighting = False
        self.count = 0

    @property
    def interval(self):
        return "1day"

    @property
    def assets(self):
        return self.tickers + self.bench

    def realized_volatility_daily(self, series_log_return):
        """
        Get the daily realized volatility which is calculated as the square root
        of sum of squares of log returns within a specific window interval
        """
        n = len(series_log_return)
        vola = np.sqrt(np.sum(series_log_return**2) / (n - 1))
        return vola

    def run(self, data):
        if len(data['ohlcv']) < 2:
            self.count += 1
            if self.count >= 30:
                self.count = 0
                if self.equal_weighting:
                    allocation_dict = {i: 1 / len(self.tickers) for i in self.tickers}
                else:
                    allocation_dict = {self.tickers[i]: self.weights[i] for i in range(len(self.tickers))}
                return TargetAllocation(allocation_dict)
            else:
                return None

        today = datetime.strptime(str(next(iter(data['ohlcv'][-1].values()))['date']), '%Y-%m-%d %H:%M:%S')
        yesterday = datetime.strptime(str(next(iter(data['ohlcv'][-2].values()))['date']), '%Y-%m-%d %H:%M:%S')

        if today.day == 11 or (today.day > 11 and yesterday.day < 11):
            if self.equal_weighting:
                allocation_dict = {i: 1 / len(self.tickers) for i in self.tickers}
            else:
                allocation_dict = {self.tickers[i]: self.weights[i] for i in range(len(self.tickers))}
            return TargetAllocation(allocation_dict)

        # Volatility switch logic
        spy_data = [entry['SPY']['close'] for entry in data['ohlcv'] if 'SPY' in entry]
        spy_dates = [entry['SPY']['date'] for entry in data['ohlcv'] if 'SPY' in entry]
        spy_data = pd.DataFrame(spy_data, columns=['close'])
        spy_data['returns'] = 100 * spy_data.close.pct_change().dropna()
        spy_data['log_returns'] = np.log(spy_data.close / spy_data.close.shift(1))
        spy_data = spy_data.fillna(0)
        INTERVAL_WINDOW = 60
        n_future = 20

        if len(spy_data) > n_future:
            spy_data['vol_current'] = spy_data.log_returns.rolling(window=INTERVAL_WINDOW).apply(self.realized_volatility_daily)
            spy_data['vol_current'] = spy_data['vol_current'].bfill()
            spy_data['vol_future'] = spy_data.log_returns.shift(n_future).fillna(0).rolling(window=INTERVAL_WINDOW).apply(self.realized_volatility_daily)
            spy_data['vol_future'] = spy_data['vol_future'].bfill()

            volaT = np.percentile(spy_data['vol_current'], 40)  # Increased threshold
            volaH = np.percentile(spy_data['vol_current'], 95)  # Increased threshold

            allocation_dict = {self.tickers[i]: self.weights[i] for i in range(len(self.tickers))}

            if (spy_data['vol_current'].iloc[-1] > spy_data['vol_future'].iloc[-1] and spy_data['vol_current'].iloc[-1] > volaT):
                if spy_data['vol_current'].iloc[-1] > volaH:
                    self.count = 10  # Reduced count to revert to risk-on more quickly
                else:
                    self.count = 5   # Reduced count to revert to risk-on more quickly
                return TargetAllocation({ticker: 0 for ticker in self.tickers})
            elif self.count < 1:
                allocation_dict = {self.tickers[i]: self.weights[i] for i in range(len(self.tickers))}
                return TargetAllocation(allocation_dict)
            else:
                self.count -= 1  # Decrement count to eventually revert to risk-on
                return TargetAllocation({ticker: 0 for ticker in self.tickers})
        else:
            return TargetAllocation({ticker: 0 for ticker in self.tickers})

        return None
