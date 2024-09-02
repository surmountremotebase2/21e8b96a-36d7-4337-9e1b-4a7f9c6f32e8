from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import EMA, ATR
from surmount.logging import log
from surmount.data import ohlcv

class TradingStrategy(Strategy):
    @property
    def assets(self):
        return ["SPY"]

    @property
    def interval(self):
        return "1day"
    
    def run(self, data):
        # Initialize allocation
        allocation = {}

        # Calculate the 7-day EMA for SPY
        ema_7 = EMA("SPY", data["ohlcv"], length=7)

        # Calculate the 30-day Keltner Channels (Middle Band is a 20-day EMA)
        keltner_middle = EMA("SPY", data["ohlcv"], length=20)
        atr_30 = ATR("SPY", data["ohlcv"], length=30)

        # Assuming typical Keltner Channel uses 2 times the ATR for the upper and lower bands
        # and the middle band as the 20-day EMA
        if ema_7 and keltner_middle and atr_30:
            upper_band = [middle + 2*atr for middle, atr in zip(keltner_middle, atr_30)]
            lower_band = [middle - 2*atr for middle, atr in zip(keltner_middle, atr_30)]
            
            # Check if 7-day EMA crosses above the middle band (BUY Signal)
            if ema_7[-2] < keltner_middle[-2] and ema_7[-1] > keltner_middle[-1]:
                log("BUY signal - EMA crossed above the middle Keltner band.")
                allocation["SPY"] = 1.0  # Assign 100% of the portfolio to SPY
            
            # Check if 7-day EMA crosses below the upper band (SELL Signal)
            elif ema_7[-2] > upper_band[-2] and ema_7[-1] < upper_band[-1]:
                log("SELL signal - EMA crossed below the upper Keltner band.")
                allocation["SPY"] = 0  # Sell off SPY, holding cash or equivalent 
            
            # No trading signal
            else:
                log("No trading action recommended based on current data.")
                allocation["SPY"] = 0  # Maintain current holding or no action

        return TargetAllocation(allocation)