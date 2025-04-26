from surmount.base_class import Strategy, TargetAllocation, backtest
from surmount.logging import log
from surmount.technical_indicators import SMA
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
        self.trading_assets = self.tickers + ["BIL"]  # Include BIL as a risk-free asset
        self.mkrt = "SPY"
        self.MinMonths = 3
        self.MaxMonths = 9
        self.WARMUP = 189  # 9 months warmup period (189 days)

    @property
    def interval(self):
        return "1day"

    @property
    def assets(self):
        return self.tickers + self.bench + ["BIL"]

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

        # Extract SPY close data
        spy_data = [entry['SPY']['close'] for entry in data['ohlcv'] if 'SPY' in entry]
        spy_dates = [entry['SPY']['date'] for entry in data['ohlcv'] if 'SPY' in entry]
        spy_close = pd.DataFrame(spy_data, index=spy_dates, columns=['close'])

        # Define moving average periods (3 to 9 months, assuming 21 trading days per month)
        ma_periods = [i * 21 for i in range(self.MinMonths, self.MaxMonths + 1)]  # 63, 84, 105, ..., 189 days

        # Initialize signals DataFrame to store buy/sell signals for each MA period
        signals = pd.DataFrame(index=spy_close.index, columns=[f"ma_{ma}" for ma in ma_periods], dtype=float)

        # Compute EMAs and signals for each period
        for ma in ma_periods:
            # SPY EMA
            spy_ema = SMA("SPY", data["ohlcv"], ma)

            # Signal: 1 if SPY is above its EMA, 0 otherwise
            signal = (spy_close['close'] > spy_ema).astype(int)

            signals[f"ma_{ma}"] = signal

        # Start after warmup period
        if len(spy_close) > self.WARMUP:
            current_signals = signals.iloc[-1]

            # Compute the average signal across all strategies (equally weighted)
            average_signal = current_signals.mean()

            # Allocate based on the average signal
            if average_signal > 0.55:
                allocation_dict = {ticker: weight for ticker, weight in zip(self.tickers, self.weights)}
            else:
                allocation_dict = {"BIL": 1}

            return TargetAllocation(allocation_dict)
        else:
            return TargetAllocation({ticker: 0 for ticker in self.tickers})

        return None