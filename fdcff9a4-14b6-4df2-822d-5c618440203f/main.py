from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import MACD, SMA, EMA
from surmount.logging import log
import pandas as pd

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
        macd_indicator = MACD("USO", data, 15, 25)
        
        # Calculate 20 day SMA for "USO"
        #sma_20 = SMA("USO", data, 18)
        sma_20 = EMA("USO", data, 18)
        sma_100 = SMA("USO", data, 100)
        
        if macd_indicator is None or sma_20 is None:
            return TargetAllocation({})
        
        MACDDF = pd.DataFrame(macd_indicator)
        MACDDFCols = MACDDF.columns
        #log(f'Macd Cols: {MACDDFCols}')   #Macd Cols: Index(['MACD_5_15_9', 'MACDh_5_15_9', 'MACDs_5_15_9'], dtype='object')
        #log(f'Macd Indi: {macd_indicator}')
        current_price = data[-1]["USO"]["close"]
        previous_macd = macd_indicator["MACD_15_25_9"][-2]
        current_macd = macd_indicator["MACD_15_25_9"][-1]
        MH = macd_indicator["MACDh_15_25_9"][-1]
        macd_signal = macd_indicator["MACDs_15_25_9"][-1]
        #log(f' MACD: {current_macd} - MH: {MH} - Signal: {macd_signal}')

        # MACD turning positive condition
        if macd_signal > 0 and current_price > sma_20[-1] and current_price > sma_100[-1]:
            #log("MACD turning positive, buying USO")
            uso_allocation = 1
        # Close position if "USO" close price crossed below the 20 days SMA or MACD turns negative
        elif current_price < sma_20[-1] and macd_signal < 0:
            #log("Closing USO position")
            uso_allocation = 0

        return TargetAllocation({"USO": uso_allocation})