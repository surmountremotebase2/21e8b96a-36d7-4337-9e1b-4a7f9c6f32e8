from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import SMA
from surmount.logging import log

class TradingStrategy(Strategy):
    def __init__(self):
        self.tickers = ["TSM", "BABA", "TCEHY", "SE", "MELI", "RELI"]

    @property
    def interval(self):
        return "1day"

    @property
    def assets(self):
        return self.tickers

    def run(self, data):
        ohlcv = data["ohlcv"]
        allocation = {ticker: 0 for ticker in self.tickers}
        total_weight = 0
        max_price = {ticker: max([candle[ticker]['close'] for candle in ohlcv]) for ticker in self.tickers}

        for ticker in self.tickers:
            if len(ohlcv) < 200:
                continue  # Ensure sufficient data

            sma_50 = SMA(ticker, ohlcv, 50)
            sma_200 = SMA(ticker, ohlcv, 200)

            if not sma_50 or not sma_200:
                continue

            current_price = ohlcv[-1][ticker]['close']
            
            # Determine overweight or underweight based on SMA
            if current_price > sma_50[-1] and current_price > sma_200[-1]:
                weight = 0.25  # Overweight allocation
            else:
                weight = 0.1  # Underweight allocation

            # Profit-taking rule
            if len(ohlcv) >= 60:  # Ensure 3 months of data
                past_price = ohlcv[-60][ticker]['close']
                if ticker in ["TSM", "MELI"] and current_price >= 1.5 * past_price:
                    #log(f"Profit-taking: Trimming {ticker}")
                    weight *= 0.5

            # Stop-loss rule
            if current_price <= 0.8 * max_price[ticker]:
                #log(f"Stop-loss: Trimming {ticker}")
                weight *= 0.5

            allocation[ticker] = weight
            total_weight += weight

        # Normalize allocations to sum <= 1
        if total_weight > 1:
            allocation = {k: v / total_weight for k, v in allocation.items()}

        return TargetAllocation(allocation)