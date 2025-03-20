from surmount.base_class import Strategy, TargetAllocation
from surmount.logging import log
from surmount.technical_indicators import STDEV
from datetime import datetime

class TradingStrategy(Strategy):
    def __init__(self):
        self.tickers = ["MSFT", "ARM", "NVDA", "AMD"]
        self.data_list = []
        self.min_days = 21  # Minimum days for basic operation (e.g., monthly stop-loss)

    @property
    def assets(self):
        return self.tickers

    @property
    def interval(self):
        return "1day"

    @property
    def data(self):
        return self.data_list

    def run(self, data):
        ohlcv = data["ohlcv"]
        if len(ohlcv) < self.min_days:
            log("Insufficient data for basic analysis")
            return TargetAllocation({ticker: 0 for ticker in self.tickers})

        # Extract closing prices
        prices = {ticker: [d[ticker]["close"] for d in ohlcv if ticker in d] for ticker in self.tickers}

        # Default to equal weights if less than 63 days
        allocation_dict = {ticker: 0.25 for ticker in self.tickers}
        if len(ohlcv) < 63:
            log("Less than 63 days, using equal weights")
            return TargetAllocation(allocation_dict)

        # Check if today is a quarter-end day (approximated as last trading day of Mar, Jun, Sep, Dec)
        latest_date = datetime.strptime(ohlcv[-1][self.tickers[0]]["date"], "%Y-%m-%d %H:%M:%S")
        is_quarter_end = latest_date.month in [3, 6, 9, 12] and latest_date.day >= 25

        if not is_quarter_end:
            log("Not a quarter-end day, maintaining prior allocation")
            return TargetAllocation(allocation_dict)  # Hold position until quarter-end

        # Quarterly rebalancing logic
        quarterly_returns = {ticker: (prices[ticker][-1] / prices[ticker][-63]) - 1 
                            if len(prices[ticker]) >= 63 else 0 for ticker in self.tickers}

        # Calculate volatility over the last quarter
        volatilities = {}
        for ticker in self.tickers:
            vol = STDEV(ticker, ohlcv[-63:], 63)
            volatilities[ticker] = vol[-1] if vol and len(vol) > 0 else 0.1

        # Inverse volatility weighting
        inverse_vol_sum = sum(1 / max(v, 0.01) for v in volatilities.values())
        allocation_dict = {ticker: (1 / max(volatilities[ticker], 0.01)) / inverse_vol_sum 
                          for ticker in self.tickers}

        # Profit-Taking Rule: NVDA or ARM up 40% in a quarter
        for ticker in ["NVDA", "ARM"]:
            if quarterly_returns[ticker] >= 0.4:
                log(f"{ticker} up 40%+, rebalancing to equal-weight")
                allocation_dict = {t: 0.25 for t in self.tickers}
                break

        # Stop-Loss Rule: AMD drops >15% in a month (21 days)
        if len(prices["AMD"]) >= 21:
            monthly_return = (prices["AMD"][-1] / prices["AMD"][-21]) - 1
            if monthly_return <= -0.15:
                log("AMD dropped >15% in a month, reducing exposure by half")
                allocation_dict["AMD"] *= 0.5
                remaining = sum(allocation_dict[t] for t in self.tickers if t != "AMD")
                for t in self.tickers:
                    if t != "AMD":
                        allocation_dict[t] = allocation_dict[t] / remaining * (1 - allocation_dict["AMD"])

        # Volatility Spike Rule: MSFT volatility 50% above historical average
        msft_vol = volatilities["MSFT"]
        msft_hist_vol = STDEV("MSFT", ohlcv, len(ohlcv))
        msft_hist_vol = msft_hist_vol[-1] if msft_hist_vol and len(msft_hist_vol) > 0 else msft_vol
        if msft_vol > msft_hist_vol * 1.5:
            log("MSFT volatility spiked 50% above average, rebalancing")
            allocation_dict = {t: 0.25 for t in self.tickers}

        # Ensure total allocation sums to 1
        total = sum(allocation_dict.values())
        if total > 0:
            allocation_dict = {t: w / total for t, w in allocation_dict.items()}

        return TargetAllocation(allocation_dict)