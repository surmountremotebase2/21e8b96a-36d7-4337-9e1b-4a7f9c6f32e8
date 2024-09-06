from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import EMA, BB, Slope, RSI
from surmount.logging import log

class TradingStrategy(Strategy):
    def __init__(self):
        self.tickers = ["SPY", "QQQ"]
        self.mrkt = "SPY"
        self.tradeAsset = "QQQ"
        self.std_dev_multiplier = .6
        self.trade = 0

    @property
    def interval(self):
        return "1day"

    @property
    def assets(self):
        return self.tickers

    def run(self, data):
        spy_ema7 = EMA(self.mrkt, data["ohlcv"], 7)
        spy_ema30 = EMA(self.mrkt, data["ohlcv"], 30)
        spy_rsi = RSI(self.mrkt, data["ohlcv"], 5)
        bb = BB(self.mrkt, data["ohlcv"], 30, self.std_dev_multiplier)
        mrktSlope = Slope(self.mrkt, data["ohlcv"], 5)
        closes = [i[self.mrkt]["close"] for i in data["ohlcv"]]


        current_price = closes[-1]
        upper_band = bb["upper"][-1]
        middle_band = bb["mid"][-1]
        lower_band = bb["lower"][-1]
        allocation = 0.0  # Default state is not to hold the asset
        

        if spy_ema7[-1] < upper_band and spy_ema7[-2] >= bb["upper"][-1]:
            #log(str(mrktSlope[-1]))
            self.trade = 0
        elif spy_ema7[-1] > lower_band and spy_ema7[-2] <= bb["lower"][-1] and spy_rsi[-1] < 50 and mrktSlope[-1] > 0:
            self.trade = 1
        elif spy_ema7[-1] >= upper_band and spy_ema7[-2] >= bb["upper"][-2] and spy_rsi[-1] > 50 and mrktSlope[-1] > 0:
            self.trade = 1
        
        if self.trade == 1:
            allocation = 1.0
        else:
            allocation = 0

        return TargetAllocation({self.tradeAsset: allocation})

# Note: This script assumes access to EMA but not directly to ATR or detailed Keltner Channel calculations.
# Adapt based on available data and true Keltner Channel calculations including ATR for accurate signals.