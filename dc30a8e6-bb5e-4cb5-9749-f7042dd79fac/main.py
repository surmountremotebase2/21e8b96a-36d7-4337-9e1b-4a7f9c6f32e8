
from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import EMA, BB, Slope
from surmount.logging import log

class TradingStrategy(Strategy):
    def __init__(self):
        self.tickers = ["SPY", "QQQ"]
        self.mrkt = "SPY"
        self.tradeAsset = "QQQ"
        self.std_dev_multiplier = 1

    @property
    def interval(self):
        return "1day"

    @property
    def assets(self):
        return self.tickers

    def run(self, data):
        spy_ema7 = EMA(self.mrkt, data["ohlcv"], 7)
        spy_ema30 = EMA(self.mrkt, data["ohlcv"], 30)
        bb = BB(self.mrkt, data["ohlcv"], 30, self.std_dev_multiplier)
        mrktSlope = Slope(self.mrkt, data["ohlcv"], 30)
        closes = [i[self.mrkt]["close"] for i in data["ohlcv"]]


        current_price = closes[-1]
        upper_band = bb["upper"][-1]
        middle_band = bb["mid"][-1]
        allocation = 0.0  # Default state is not to hold the asset
        

        # Check if EMA7 crosses above the middle band (EMA30 here) for a BUY signal
        if spy_ema7[-1] > middle_band and spy_ema7[-2] <= bb["mid"][-2]:
            allocation = 1.0  # BUY condition

        elif spy_ema7[-1] < upper_band and spy_ema7[-2] >= bb["upper"][-2]:  # This condition is contrary to the usual use of Keltner and might need adjustment for a real strategy
            allocation = 0.0  # SELL condition
            log(str(mrktSlope[-1]))

        return TargetAllocation({self.tradeAsset: allocation})

# Note: This script assumes access to EMA but not directly to ATR or detailed Keltner Channel calculations.
# Adapt based on available data and true Keltner Channel calculations including ATR for accurate signals.
