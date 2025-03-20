from surmount.base_class import Strategy, TargetAllocation
from surmount.logging import log
from surmount.technical_indicators import STDEV
import pandas as pd

class TradingStrategy(Strategy):
    def __init__(self):
        # Define the assets: Microsoft, ARM, NVIDIA, and ORIC Pharmaceuticals
        self.tickers = ["MSFT", "ARM", "NVDA", "ORCI"]
        self.data_list = []

    @property
    def assets(self):
        return self.tickers

    @property
    def interval(self):
        # Use daily data for volatility calculations; quarterly rebalancing checked via date
        return "1day"

    @property
    def data(self):
        return self.data_list

    def run(self, data):
        ohlcv = data["ohlcv"]
        if len(ohlcv) < 63:  # Approx. 3 months (quarter) of trading days
            log("Insufficient data for quarterly analysis")
            return TargetAllocation({ticker: 0 for ticker in self.tickers})

        # Extract closing prices and calculate quarterly returns
        prices = {ticker: [d[ticker]["close"] for d in ohlcv if ticker in d] for ticker in self.tickers}
        quarterly_returns = {}
        for ticker in self.tickers:
            if len(prices[ticker]) >= 63:
                quarterly_returns[ticker] = (prices[ticker][-1] / prices[ticker][-63]) - 1
            else:
                quarterly_returns[ticker] = 0

        # Calculate volatility (standard deviation) over the last quarter
        volatilities = {}
        for ticker in self.tickers:
            vol = STDEV(ticker, ohlcv[-63:], 63)
            volatilities[ticker] = vol[-1] if vol and len(vol) > 0 else 0.1  # Default small vol if missing

        # Inverse volatility weighting
        inverse_vol_sum = sum(1 / max(v, 0.01) for v in volatilities.values())  # Avoid division by zero
        base_weights = {ticker: (1 / max(volatilities[ticker], 0.01)) / inverse_vol_sum 
                       for ticker in self.tickers}

        # Adjust weights based on rules
        allocation_dict = base_weights.copy()

        # Profit-Taking Rule: NVDA or ARM up 40% in a quarter
        for ticker in ["NVDA", "ARM"]:
            if quarterly_returns[ticker] >= 0.4:
                log(f"{ticker} up 40%+, rebalancing to equal-weight")
                allocation_dict = {t: 0.25 for t in self.tickers}  # Equal-weight reset
                break

        # Stop-Loss Rule: ORCI drops >15% in a month (approx 21 trading days)
        if len(prices["ORCI"]) >= 21:
            monthly_return = (prices["ORCI"][-1] / prices["ORCI"][-21]) - 1
            if monthly_return <= -0.15:
                log("ORCI dropped >15% in a month, reducing exposure by half")
                allocation_dict["ORCI"] *= 0.5
                # Redistribute remaining weight proportionally
                remaining = sum(allocation_dict[t] for t in self.tickers if t != "ORCI")
                for t in self.tickers:
                    if t != "ORCI":
                        allocation_dict[t] = allocation_dict[t] / remaining * (1 - allocation_dict["ORCI"])

        # Volatility Spike Rule: MSFT volatility 50% above historical average
        msft_vol = volatilities["MSFT"]
        msft_hist_vol = STDEV("MSFT", ohlcv, len(ohlcv))[-1] if len(ohlcv) > 63 else msft_vol
        if msft_vol > msft_hist_vol * 1.5:
            log("MSFT volatility spiked 50% above average, rebalancing")
            allocation_dict = {t: 0.25 for t in self.tickers}  # Equal-weight reset

        # Ensure total allocation sums to 1
        total = sum(allocation_dict.values())
        if total > 0:
            allocation_dict = {t: w / total for t, w in allocation_dict.items()}

        return TargetAllocation(allocation_dict)