from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import RSI, EMA
from surmount.logging import log

class TradingStrategy(Strategy):
    def __init__(self):
        # Only trading with "USO" ETF
        self.ticker = "USO"

    @property
    def assets(self):
        # Defines the asset to trade
        return [self.ticker]

    @property
    def interval(self):
        # Sets the strategy to run on daily data
        return "1day"

    def run(self, data):
        # The trading logic goes here
        
        # Initialize allocation to 0, assuming not to take any position by default
        uso_allocation = 0
        
        # Define the lookback periods for the technical indicators
        short_term_lookback = 10  # Short-term EMA
        long_term_lookback = 100  # Long-term EMA
        rsi_period = 30  # Relative Strength Index period
        
        # Calculate EMAs and RSI for USO
        short_term_ema = EMA(self.ticker, data["ohlcv"], short_term_lookback)
        long_term_ema = EMA(self.ticker, data["ohlcv"], long_term_lookback)
        rsi = RSI(self.ticker, data["ohlcv"], rsi_period)
        
        # Ensure we have enough data to consider a position
        if short_term_ema is not None and long_term_ema is not None and rsi is not None:
            # Check if current short-term EMA is above long-term EMA, representing an uptrend
            if short_term_ema[-1] > long_term_ema[-1]:
                # Additionally, check if RSI is indicating strong momentum but not overbought
                if rsi[-1] > 50 and rsi[-1] < 70:
                    # If both conditions are met, set allocation to 1 (i.e., 100% of portfolio)
                    uso_allocation = 1
                    
                    # Logging for analysis
                    log(f"USO Allocation: {uso_allocation}, Short EMA: {short_term_ema[-1]}, Long EMA: {long_term_ema[-1]}, RSI: {rsi[-1]}")
        
        # Return the allocation object with the calculated allocation
        return TargetAllocation({self.ticker: uso_allocation})