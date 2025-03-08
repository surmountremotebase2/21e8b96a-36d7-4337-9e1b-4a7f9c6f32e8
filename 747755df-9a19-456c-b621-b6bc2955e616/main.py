from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import MACD
from surmount.logging import log
import pandas as pd
import numpy as np

class TradingStrategy(Strategy):
    def __init__(self):
        self.tickers = ["GLD"]
        self.entry_tick = {}
        self.exit_date = {}
        self.initial_prices = {}
    
    @property
    def assets(self):
        return self.tickers
    
    @property
    def interval(self):
        return "1day"
    
    def HMA(self, data, length):
        """Calculate Hull Moving Average"""
        # Calculate WMA for the half length of the data
        wma_half = data.rolling(window=int(length / 2)).mean()
        # Calculate WMA for the full length
        wma_full = data.rolling(window=length).mean()
        # Calculate the Hull Moving Average
        hma = (2 * wma_half - wma_full).rolling(window=int(np.sqrt(length))).mean()
        return hma

    def run(self, data):
        allocation_dict = {}
        for ticker in self.tickers:
            allocation_dict[ticker] = 0.0  # Default to no position
            ohlcv = pd.DataFrame(data["ohlcv"])
            prices = ohlcv[ticker]["close"]
            high = ohlcv[ticker]["high"]
            low = ohlcv[ticker]["low"]
            open = ohlcv[ticker]["open"]
            
            # Check if we have enough data for MACD and HMA
            if len(prices) > 34:  # Needs at least 34 days for HMA(15) based on calculation steps
                macd = MACD(ticker, ohlcv, 12, 26)
                hma = self.HMA(prices, 15)
               
                if ticker not in self.entry_tick:
                    if macd["MACD"][-1] > 0 and macd["histogram"][-1] > 0 and macd["histogram"][-2] < 0 and hma[-1] > hma[-2]:
                        self.entry_tick[ticker] = len(ohlcv)  # Save entry tick for duration calculation
                        self.initial_prices[ticker] = prices.iloc[-1]  # Save the initial price for stop-loss calculation
                        allocation_dict[ticker] = 1.0  # Take a position
                        self.exit_date[ticker] = len(ohlcv) + 10  # Set an exit tick after 10 trading days
                        
                elif ticker in self.entry_tick:
                    current_price = prices.iloc[-1]
                    if len(ohlcv) - self.entry_tick[ticker] >= 3:  # Check last 3 days for bullish condition
                        if all(close > open for close, open in zip(high[-3:], low[-3:])) or len(ohlcv) >= self.exit_date[ticker]:
                            allocation_dict[ticker] = 0  # Time to sell
                            del self.entry_tick[ticker]  # Reset entry tick

                    # Implementing the 5-loss
                    if current_price <= self.initial_prices[ticker] * 0.95:
                        allocation_dict[ticker] = 0  # Stop loss triggered
                        if ticker in self.entry_tick: del self.entry_tick[ticker]  # Reset entry tick if stop loss is triggered
                    
        return TargetAllocation(allocation_dict)