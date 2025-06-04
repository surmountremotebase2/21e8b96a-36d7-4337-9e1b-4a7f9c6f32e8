from surmount.base_class import Strategy, TargetAllocation
from surmount.data import PE, PEG, Asset
from surmount.technical_indicators import STDEV
import pandas as pd

class TradingStrategy(Strategy):
    def __init__(self):
        # Define a fixed basket of 10 high market cap stocks from NASDAQ/NYSE plus GLD
        self.tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'JPM', 'JNJ', 'V', 'GLD']
        # Specify data sources: SPY for volatility, PE and PEG for valuation
        self.data_list = [Asset("SPY")] + [PE(i) for i in self.tickers] + [PEG(i) for i in self.tickers]

    @property
    def assets(self):
        # Return the list of tickers including GLD
        return self.tickers

    @property
    def interval(self):
        # Use daily data for long-term allocation
        return "1day"

    @property
    def data(self):
        # Return the list of additional data sources
        return self.data_list

    def run(self, data):
        # Check if there is enough data (252 trading days ~ 1 year)
        if len(data["ohlcv"]) < 1:
            return TargetAllocation({ticker: 0 for ticker in self.tickers})

        # Dictionaries to store momentum and value scores
        momentum = {}
        value_score = {}

        # Calculate momentum (12-month return) and value score (-PEG) for stocks (excluding GLD)
        stock_tickers = [t for t in self.tickers if t != 'GLD']
        for ticker in stock_tickers:
            close_prices = [d[ticker]["close"] for d in data["ohlcv"]]
            # Momentum: 12-month return
            return_12m = (close_prices[-1] / close_prices[-252]) - 1
            momentum[ticker] = return_12m
            # Value: Negative PEG (lower PEG is better)
            try:
                peg = data[("peg", ticker)][-1]["value"]
                value_score[ticker] = -peg if peg > 0 else -1000  # Penalize non-positive PEG
            except (KeyError, IndexError):
                value_score[ticker] = -1000  # Handle missing PEG data

        # Standardize scores
        momentum_values = list(momentum.values())
        value_score_values = list(value_score.values())
        
        mean_momentum = sum(momentum_values) / len(momentum_values) if momentum_values else 0
        std_momentum = (sum((x - mean_momentum)**2 for x in momentum_values) / len(momentum_values))**0.5 if momentum_values else 1
        
        mean_value = sum(value_score_values) / len(value_score_values) if value_score_values else 0
        std_value = (sum((x - mean_value)**2 for x in value_score_values) / len(value_score_values))**0.5 if value_score_values else 1

        # Compute z-scores, handling zero standard deviation
        z_momentum = {ticker: (momentum[ticker] - mean_momentum) / std_momentum if std_momentum > 0 else 0 
                      for ticker in stock_tickers}
        z_value = {ticker: (value_score[ticker] - mean_value) / std_value if std_value > 0 else 0 
                   for ticker in stock_tickers}

        # Combined score: 50% momentum, 50% value
        combined_score = {ticker: 0.5 * z_momentum[ticker] + 0.5 * z_value[ticker] 
                          for ticker in stock_tickers}

        # Allocate weights to stocks with positive scores
        positive_scores = {ticker: score for ticker, score in combined_score.items() if score > 0}
        stock_allocation = {}
        if positive_scores:
            total_positive = sum(positive_scores.values())
            stock_allocation = {ticker: score / total_positive if ticker in positive_scores else 0 
                                for ticker in stock_tickers}
        else:
            stock_allocation = {ticker: 0 for ticker in stock_tickers}

        # Calculate SPY realized volatility (21-day standard deviation of daily returns)
        spy_prices = [d["SPY"]["close"] for d in data["ohlcv"][-252:]]
        spy_returns = [(spy_prices[i] / spy_prices[i-1] - 1) for i in range(1, len(spy_prices))]
        realized_vol = STDEV("SPY", data["ohlcv"], 21)[-1] * (252 ** 0.5) if len(data["ohlcv"]) >= 21 else 0.2

        # Protective mechanism: Scale allocation based on SPY realized volatility
        if realized_vol < 0.15:
            scaling = 1.0    # Low volatility: full allocation to stocks
            gld_allocation = 0.0
        elif realized_vol < 0.25:
            scaling = 0.5    # Moderate volatility: 50% to stocks, 50% to GLD
            gld_allocation = 0.5
        else:
            scaling = 0.0    # High volatility: 0% to stocks, 100% to cash (no allocation)
            gld_allocation = 0.0

        # Final allocation: Scale stock allocations and assign remainder to GLD or cash
        allocation_dict = {ticker: stock_allocation[ticker] * scaling for ticker in stock_tickers}
        allocation_dict['GLD'] = gld_allocation

        # Ensure sum of allocations is between 0 and 1
        total_allocation = sum(allocation_dict.values())
        if total_allocation > 1:
            allocation_dict = {ticker: alloc / total_allocation for ticker, alloc in allocation_dict.items()}
        elif total_allocation == 0:
            allocation_dict = {ticker: 0 for ticker in self.tickers}  # All to cash (no allocation)

        return TargetAllocation(allocation_dict)