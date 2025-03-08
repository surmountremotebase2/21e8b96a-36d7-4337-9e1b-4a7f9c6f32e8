from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import MACD, EMA
from surmount.logging import log
from surmount.data import OHLCV

import pandas as pd

class TradingStrategy(Strategy):
    def __init__(self):
        self.ticker = "GLD"  # Trading GLD
        self.entry_signal = False
        self.days_since_entry = 0
        self.bullish_days = 0
        self.initial_price = 0

    @property
    def assets(self):
        return [self.ticker]

    @property
    def interval(self):
        return "1day"

    def hma(self, data, length=15):
        """Calculate an approximate Hull Moving Average."""
        # Given this package does not have HMA, we approximate with a faster EMA
        half_length_ema = EMA(self.ticker, data, length // 2)
        full_length_ema = EMA(self.ticker, data, length)
        if not half_length_ema or not full_length_ema:
            return None
        approx_hma = 2 * pd.Series(half_length_ema) - pd.Series(full_length_ema)
        return approx_hma.diff().iloc[-1] > 0  # Check if HMA is sloping upwards

    def run(self, data):
        ohlcv = data["ohlcv"]
        
        macd_data = MACD(self.ticker, ohlcv, 12, 26)
        current_macd_line = macd_data["MACD"][-1]
        current_histogram = macd_data["histogram"][-1]
        previous_histogram = macd_data["histogram"][-2]
        
        # Check for an upward sloping HMA
        hma_upwards = self.hma(ohlcv, 15)
        
        if current_macd_line > 0 and current_histogram > 0 and previous_histogram < 0 and hma_upwards:
            self.entry_signal = True
            self.initial_price = ohlcv[-1][self.ticker]["close"]
            allocation = {"GLD": 1.0}  # Enter the position
        else:
            allocation = {"GLD": 0}  # Stay out of the market
        
        if self.entry_signal:
            self.days_since_entry += 1
            current_price = ohlcv[-1][self.ticker]["close"]
            if current_price >= ohlcv[-2][self.ticker]["close"]:
                self.bullish_days += 1
            else:
                self.bullish_days = 0

            # Check exit conditions
            if self.bullish_days >= 3 or self.days_since_entry >= 10 or current_price <= self.initial_price * 0.95:
                allocation = {"GLD": 0}  # Exit the position
                self.reset()  # Reset trading flags and counters for the next trade
        
        return TargetAllocation(allocation)

    def reset(self):
        """Resets trading flags and counters."""
        self.entry_signal = False
        self.days_since_entry = 0
        self.bullish_days = 0
        self.initial_price = 0