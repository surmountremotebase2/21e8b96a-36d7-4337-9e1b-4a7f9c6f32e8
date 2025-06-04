from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import SMA, RSI
from surmount.logging import log
import numpy as np

class TradingStrategy(Strategy):
    def __init__(self):
        self.tickers = ["XLK", "XLV", "XLF", "XLI", "XLY", 
                        "XLP", "XLE", "XLU", "XLB", "XLRE"]
        self.safe_asset = "GLD"
        self.target_vol = 0.15  # 15% annualized volatility
        self.lookback_vol = 20
        self.sma_period = 50
        self.rsi_period = 14

    @property
    def interval(self):
        return "1day"

    @property
    def assets(self):
        return self.tickers + [self.safe_asset]

    @property
    def data(self):
        return []

    def annualized_volatility(self, prices):
        if len(prices) < self.lookback_vol + 1:
            return None
        returns = np.diff(np.log(prices[-self.lookback_vol-1:]))
        if not np.all(np.isfinite(returns)):
            return None
        return float(np.std(returns) * np.sqrt(252))

    def run(self, data):
        price_data = data["ohlcv"]
        allocations = {}
        vol_weights = {}

        for ticker in self.tickers:
            try:
                if len(price_data) < self.sma_period + self.lookback_vol + 1:
                    continue

                prices = [bar[ticker]["close"] for bar in price_data]
                sma = SMA(ticker, price_data, self.sma_period)
                rsi = RSI(ticker, price_data, self.rsi_period)
                latest_close = prices[-1]

                if sma is None or rsi is None or len(sma) < 1 or len(rsi) < 1:
                    continue

                if latest_close > sma[-1] and rsi[-1] < 70:
                    vol = self.annualized_volatility(prices)
                    if vol and vol > 0:
                        weight = self.target_vol / vol
                        if np.isfinite(weight):
                            vol_weights[ticker] = float(weight)

            except Exception as e:
                log(f"Error processing {ticker}: {e}")

        if not vol_weights:
            return TargetAllocation({self.safe_asset: 1.0})

        total = sum(vol_weights.values())
        if total <= 0 or not np.isfinite(total):
            return TargetAllocation({self.safe_asset: 1.0})

        for ticker, weight in vol_weights.items():
            allocations[ticker] = float(weight / total)

        return TargetAllocation(allocations)