from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import SMA, BB
from surmount.data import Asset
from surmount.logging import log

class TradingStrategy(Strategy):
    def __init__(self):
        # Define the assets this strategy will handle: BTCUSD, GLD, and QQQ for trading signals and actions.
        self.tickers = ["QQQ", "BTCUSD", "GLD"]
        
        # Only QQQ is traded based on signals derived from BTCUSD/GLD ratio, so no direct data requirement for QQQ in data_list
        self.data_list = [Asset("BTCUSD"), Asset("GLD")]  # BTCUSD and GLD data are used for signals
        
    @property
    def interval(self):
        # Daily interval for generating signals and trading actions
        return "1day"
    
    @property
    def assets(self):
        # QQQ is the asset that will be traded in this strategy
        return ["QQQ"]

    def run(self, data):
        # Initialize QQQ stake to 0, meaning no position by default
        qqq_stake = 0

        # Ensure there's enough data for BTCUSD, GLD, and QQQ to generate signals
        if len(data["ohlcv"]) < 100:
            log("Insufficient data length.")
            return TargetAllocation({"QQQ": qqq_stake})

        # Calculate the ratio of BTCUSD to GLD
        btcusd_prices = [x["BTCUSD"]["close"] for x in data["ohlcv"]]
        gld_prices = [x["GLD"]["close"] for x in data["ohlcv"]]
        ratio = [btc/gld for btc, gld in zip(btcusd_prices, gld_prices)]

        # Calculate moving averages and Bollinger Bands for the ratio
        ratio_sma20 = SMA("ratio", {"ratio": {"close": ratio}}, 20)
        ratio_sma100 = SMA("ratio", {"ratio": {"close": ratio}}, 100)
        ratio_bb20 = BB("ratio", {"ratio": {"close": ratio}}, 20, 1.4)

        # Check if the current 20-day SMA and the lower Bollinger band are above the 100-day SMA, indicating a buy signal
        if ratio_sma20[-1] > ratio_sma100[-1] and ratio_bb20["lower"][-1] > ratio_sma100[-1]:
            log("Buy signal detected.")
            qqq_stake = 1  # Allocating 100% to QQQ based on the buy signal

        # Check if the current 20-day SMA or the lower Bollinger band cross below the 100-day SMA, indicating a sell signal
        elif ratio_sma20[-1] < ratio_sma100[-1] or ratio_bb20["lower"][-1] < ratio_sma100[-1]:
            log("Sell signal detected.")
            qqq_stake = 0  # Selling QQQ and going to cash

        # Return the target allocation for QQQ based on the calculated signals
        return TargetAllocation({"QQQ": qqq_stake})