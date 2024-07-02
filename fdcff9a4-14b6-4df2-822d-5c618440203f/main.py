
from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import MACD, SMA
from surmount.logging import log

class TradingStrategy(Strategy):

    @property
    def assets(self):
        return ["USO"]

    @property
    def interval(self):
        return "1day"

    def run(self, data):
        uso_allocation = 0
        data = data["ohlcv"]
        
        # Calculate MACD with fast=5 and slow=15
        macd_indicator = MACD("USO", data, 5, 15)
        
        # Calculate 20 day SMA for "USO"
        sma_20 = SMA("USO", data, 20)
        
        if macd_indicator is None or sma_20 is None:
            return TargetAllocation({})
        
        #log(f'Macd Indi: {macd_indicator}')
        current_price = data[-1]["USO"]["close"]
        previous_macd = macd_indicator["MACD_5_15_9"][-2]
        current_macd = macd_indicator["MACD_5_15_9"][-1]
        macd_signal = macd_indicator["signal"][-1]

        # MACD turning positive condition
        if current_macd > macd_signal and previous_macd <= macd_signal:
            log("MACD turning positive, buying USO")
            uso_allocation = 1
        # Close position if "USO" close price crossed below the 20 days SMA or MACD turns negative
        elif current_price < sma_20[-1] or current_macd < macd_signal:
            log("Closing USO position")
            uso_allocation = 0

        return TargetAllocation({"USO": uso_allocation})
