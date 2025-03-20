from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import STDEV
from surmount.logging import log
import numpy as np

class TradingStrategy(Strategy):
    def __init__(self):
        self.tickers = ["MSFT", "NVDA", "ARM", "ORCI"]

    @property
    def interval(self):
        return "1day"

    @property
    def assets(self):
        return self.tickers

    @property
    def data(self):
        return []

    def inverse_volatility_weights(self, data):
        """Calculate inverse volatility weights."""
        volatilities = {ticker: STDEV(ticker, data, 30)[-1] for ticker in self.tickers if ticker in data["ohlcv"][-1]}
        if not volatilities:
            return {ticker: 1 / len(self.tickers) for ticker in self.tickers}  # Fallback to equal weight
        inverse_vol = {ticker: 1 / vol for ticker, vol in volatilities.items() if vol > 0}
        total_inv_vol = sum(inverse_vol.values())
        return {ticker: inv_vol / total_inv_vol for ticker, inv_vol in inverse_vol.items()}

    def run(self, data):
        """Execute the trading strategy."""
        ohlcv = data["ohlcv"]
        allocations = self.inverse_volatility_weights(ohlcv)

        # Apply profit-taking rule
        for ticker in ["NVDA", "ARM"]:
            if ticker in ohlcv[-1] and ticker in ohlcv[-21]:
                if ohlcv[-1][ticker]["close"] >= 1.4 * ohlcv[-21][ticker]["close"]:
                    #log(f"{ticker} up 40% in a quarter, rebalancing to equal weight.")
                    allocations = {t: 1 / len(self.tickers) for t in self.tickers}
                    break

        # Apply stop-loss rules
        if "ORCI" in ohlcv[-1] and "ORCI" in ohlcv[-21]:
            if ohlcv[-1]["ORCI"]["close"] <= 0.85 * ohlcv[-21]["ORCI"]["close"]:
                #log("ORCI dropped >15% in a month, reducing exposure by half.")
                allocations["ORCI"] = allocations.get("ORCI", 0) / 2
        
        if "MSFT" in ohlcv[-1]:
            msft_volatility = STDEV("MSFT", ohlcv, 30)[-1]
            historical_avg_vol = np.mean(STDEV("MSFT", ohlcv, 90))
            if msft_volatility > 1.5 * historical_avg_vol:
                #log("MSFT volatility spiked 50% above historical average, rebalancing.")
                allocations = {t: 1 / len(self.tickers) for t in self.tickers}
        
        return TargetAllocation(allocations)