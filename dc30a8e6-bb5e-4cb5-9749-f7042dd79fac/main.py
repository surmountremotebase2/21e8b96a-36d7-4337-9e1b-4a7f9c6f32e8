from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import EMA, BB, Slope, RSI
from surmount.logging import log

class TradingStrategy(Strategy):
    def __init__(self):
        self.tickers = ["SPY", "QQQ", "TQQQ"]
        #self.tickers = ["SPY", "QQQ"]
        self.mrkt = "QQQ"
        self.tradeAsset1 = "QQQ"
        self.tradeAsset2 = "TQQQ"
        self.std_dev_multiplier = .6
        self.trade = 0
        self.count = 0

    @property
    def interval(self):
        return "1day"

    @property
    def assets(self):
        return self.tickers

    def run(self, data):
        spy_ema7 = EMA(self.mrkt, data["ohlcv"], 7)
        spy_ema30 = EMA(self.mrkt, data["ohlcv"], 30)
        spy_ema200 = EMA(self.mrkt, data["ohlcv"], 200)
        spy_rsi = RSI(self.mrkt, data["ohlcv"], 5)
        bb = BB(self.mrkt, data["ohlcv"], 30, self.std_dev_multiplier)
        mrktSlope = Slope(self.mrkt, data["ohlcv"], 110)
        mrktSlopeS = Slope(self.mrkt, data["ohlcv"], 15)
        closes = [i[self.mrkt]["close"] for i in data["ohlcv"]]
        self.count =- 1


        current_price = closes[-1]
        upper_band = bb["upper"][-1]
        middle_band = bb["mid"][-1]
        lower_band = bb["lower"][-1]
        allocation = 0.0  # Default state is not to hold the asset
        
        if spy_ema7[-1] < upper_band and spy_ema7[-5] >= bb["upper"][-5] and spy_ema7[-3] >= lower_band and (mrktSlopeS[-1] < 0 or spy_rsi[-1] > 60):
        #if spy_ema7[-1] < middle_band and spy_ema7[-5] >= bb["upper"][-5]:
            #log("OFF #1")
            #log(str(mrktSlope[-1]))
            self.trade = 0
            self.count = 15

        elif spy_ema7[-1] < lower_band and spy_ema7[-3] <= bb["lower"][-3] and spy_rsi[-1] < 40 and mrktSlope[-1] < 0:
            #log("OFF #2")
            self.trade = 0
            self.count = 5


        elif spy_ema7[-1] > lower_band and spy_ema7[-3] <= bb["lower"][-3] and (spy_rsi[-3] < 50) and self.count < 1:
            self.trade = 1
        elif spy_ema7[-1] >= upper_band and spy_ema7[-2] >= bb["upper"][-2] and spy_rsi[-1] >= 70 and mrktSlopeS[-1] > 0 and self.count < 1:
            self.trade = 1
            #log("LONG #2")
            #log(str(spy_rsi[-1]))
            #self.count = 0


        
        if self.trade == 1:
            allocation1 = .7
            allocation2 = .3
        else:
            allocation1 = 0
            allocation2 = 0

        #return TargetAllocation({self.tradeAsset1: allocation1, self.tradeAsset2: allocation2})
        return TargetAllocation({self.tradeAsset1: allocation1})

# Note: This script assumes access to EMA but not directly to ATR or detailed Keltner Channel calculations.
# Adapt based on available data and true Keltner Channel calculations including ATR for accurate signals.