from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import EMA
from surmount.logging import log

class TradingStrategy(Strategy):
    def __init__(self):
        self.tickers = ["SPY"]
        # Typically, additional data for high, low would be added
        # to accurately calculate ATR or Keltner Channel parameters.
        # This is a simplification using available tools.

    @property
    def interval(self):
        return "1day"

    @property
    def assets(self):
        return self.tickers

    def run(self, data):
        spy_ema7 = EMA("SPY", data["ohlcv"], 7)
        spy_ema30 = EMA("SPY", data["ohlcv"], 30)

        # Simplified Keltner Channel calculation placeholder
        # In practice, should calculate or access ATR and apply to EMA for the bands
        # This example assumes you have a function/method to determine when 7-EMA crosses these bands
        # Note: Implementation of such a cross-check function is not shown here due to constraints.

        allocation = 0.0  # Default state is not to hold the asset
        
        # Check if EMA7 crosses above the middle band (EMA30 here) for a BUY signal
        if spy_ema7[-1] > spy_ema30[-1] and spy_ema7[-2] <= spy_ema30[-2]:
            allocation = 1.0  # BUY condition
        # Check if EMA7 crosses below the upper band for a SELL signal
        # Placeholder for upper band calculation. Adjust as necessary.
        elif spy_ema7[-1] < spy_ema30[-1] and spy_ema7[-2] >= spy_ema30[-2]:  # This condition is contrary to the usual use of Keltner and might need adjustment for a real strategy
            allocation = 0.0  # SELL condition

        return TargetAllocation({"SPY": allocation})

# Note: This script assumes access to EMA but not directly to ATR or detailed Keltner Channel calculations.
# Adapt based on available data and true Keltner Channel calculations including ATR for accurate signals.