from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import EMA, SMA, BB
from surmount.data import Asset
from surmount.logging import log
import pandas as pd
import numpy as np

class TradingStrategy(Strategy):
    def __init__(self):
        # Define the assets this strategy will handle: BTCUSD, GLD, and QQQ for trading signals and actions.
        self.tickers = ["QQQ", "SPY", "GLD", "BIL", "SLV", "RSP"]
        self.mrkt = "SPY"
        self.count = 5
        # Only QQQ is traded based on signals derived from BTCUSD/GLD ratio, so no direct data requirement for QQQ in data_list
        self.data_list = [Asset("SPY"), Asset("GLD")]  # BTCUSD and GLD data are used for signals
        
    @property
    def interval(self):
        # Daily interval for generating signals and trading actions
        return "1day"
    
    @property
    def assets(self):
        # QQQ is the asset that will be traded in this strategy
        return self.tickers

    def realized_volatility_daily(self, series_log_return):
        """
        Get the daily realized volatility which is calculated as the square root
        of sum of squares of log returns within a specific window interval 
        """
        n = len(series_log_return)
        vola =  np.sqrt(np.sum(series_log_return**2)/(n - 1))
        return vola

    def run(self, data):
        # Initialize QQQ stake to 0, meaning no position by default
        self.count += 1
        alloc = {}
        alloc["QQQ"] = 1
        INTERVAL_WINDOW = 82

        # Ensure there's enough data for BTCUSD, GLD, and QQQ to generate signals
        if len(data["ohlcv"]) < 100:
            log("Insufficient data length.")
            return TargetAllocation({"QQQ": qqq_stake})

        # Calculate the ratio of BTCUSD to GLD
        spy_prices = [x["SPY"]["close"] for x in data["ohlcv"]]
        gld_prices = [x["GLD"]["close"] for x in data["ohlcv"]]
        slv_prices = [x["SLV"]["close"] for x in data["ohlcv"]]
        spyDF = pd.DataFrame(spy_prices, columns=["close"])
        gldDF = pd.DataFrame(gld_prices, columns=["close"])
        slvDF = pd.DataFrame(slv_prices, columns=["close"])
        spy_ret = np.log(spyDF.close/spyDF.close.shift(1))
        spyvola = spy_ret.rolling(window=INTERVAL_WINDOW).apply(self.realized_volatility_daily) * 100
        LongMA = int(82 * (1 - spyvola.iloc[-1]))
        if LongMA <= 10:
            LongMA = int(spyvola.iloc[-1] * 10)

        ratio = [spy/gld for spy, gld in zip(spy_prices, gld_prices)]

        # Calculate moving averages and Bollinger Bands for the ratio
        # ratioT = {"ratio": {"close": ratio}}
        ratioDF = pd.DataFrame(ratio, columns=["ratio"])
        ratioMAS = ratioDF["ratio"].rolling(3).mean().fillna(0)
        ratioMAL = ratioDF["ratio"].rolling(LongMA).mean().fillna(0)
        spyLongMA = int(LongMA * 3)
        slvm = slvDF.close.pct_change(45).iloc[-1]
        gldm = gldDF.close.pct_change(45).iloc[-1]
        spym = spyDF.close.pct_change(82).iloc[-1] - spyDF.close.pct_change(21).iloc[-1]
        mrktMAS = EMA("SPY", data["ohlcv"], 5)
        mrktMAL = EMA("SPY", data["ohlcv"], 20)

        # Check if the current 20-day SMA and the lower Bollinger band are above the 100-day SMA, indicating a buy signal
        #if ratioMAS.iloc[-1] > ratioMAL.iloc[-1] and mrktMAS[-1] > mrktMAL[-1]:
        if ratioMAS.iloc[-1] > ratioMAL.iloc[-1] and (slvm > gldm or mrktMAS[-1] > mrktMAL[-1]) and self.count > 10:
            #log("Buy signal detected.")
            #log(f"spyvola: {spyvola.iloc[-1]}  -- LongMA: {LongMA}")
            qqq_stake = 1  # Allocating 100% to QQQ based on the buy signal
            alloc["QQQ"] = 1
            alloc["BIL"] = 0

        # Check if the current 20-day SMA or the lower Bollinger band cross below the 100-day SMA, indicating a sell signal
        elif ratioMAS.iloc[-1] <= ratioMAL.iloc[-1] and mrktMAS[-1] < mrktMAL[-1]:
            #log("Sell signal detected.")
            #log(f"spyvola: {spyvola.iloc[-1]}  -- LongMA: {LongMA}")
            self.count = 0  # Selling QQQ and going to cash
            alloc["QQQ"] = 0
            alloc["BIL"] = 1



        # Return the target allocation for QQQ based on the calculated signals
        return TargetAllocation(alloc)