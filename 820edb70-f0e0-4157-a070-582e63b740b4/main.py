from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import SMA, RSI
from surmount.logging import log
import numpy as np

class TradingStrategy(Strategy):
    def __init__(self):
        self.tickers = ["XLK", "XLV", "XLF", "XLI", "XLY", 
                        "XLP", "XLE", "XLU", "XLB", "XLRE"]
        self.safe_asset = "GLD"
        self.target_vol = 0.15  # 15% annualized vol
        self.lookback_vol = 20  # 20-day realized vol
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
        """Estimate annualized volatility using 20-day rolling std of log returns."""
        if len(prices) < self.lookback_vol + 1:
            return None
        returns = np.diff(np.log(prices[-self.lookback_vol-1:]))
        if np.any(np.isnan(returns)):
            return None
        return np.std(returns) * np.sqrt(252)

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

                # Entry condition: above trend and not overbought
                if latest_close > sma[-1] and rsi[-1] < 70:
                    vol = self.annualized_volatility(prices)
                    if vol is not None and vol > 0:
                        # Volatility targeting weight
                        vol_weights[ticker] = self.target_vol / vol

            except Exception as e:
                log(f"Error processing {ticker}: {e}")

        if not vol_weights:
            # No qualifying sectors — move fully to GLD
            return TargetAllocation({self.safe_asset: 1.0})

        # Normalize total to max 1.0
        total = sum(vol_weights.values())
        for ticker, weight in vol_weights.items():
            allocations[ticker] = weight / total

        return TargetAllocation(allocations)