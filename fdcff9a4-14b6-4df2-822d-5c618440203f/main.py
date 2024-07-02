from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import MACD, SMA, EMA, BB, RSI
from surmount.logging import log
import pandas as pd

class TradingStrategy(Strategy):

    @property
    def assets(self):
        return ["USO", "SCO"]

    @property
    def interval(self):
        return "1day"

    def run(self, data):
        uso_allocation = 0
        data = data["ohlcv"]
        
        # Calculate MACD with fast=5 and slow=15
        macd_indicator = MACD("USO", data, 15, 40)

        MACDDF = pd.DataFrame(macd_indicator)
        MACDDFCols = MACDDF.columns
        #log(f'Macd Cols: {MACDDFCols}')   #Macd Cols: Index(['MACD_5_15_9', 'MACDh_5_15_9', 'MACDs_5_15_9'], dtype='object')
        #log(f'Macd Indi: {macd_indicator}')
        current_price = data[-1]["USO"]["close"]
        previous_macd = macd_indicator["MACD_15_40_9"][-2]
        current_macd = macd_indicator["MACD_15_40_9"][-1]
        MH = macd_indicator["MACDh_15_40_9"][-1]
        macd_signal = macd_indicator["MACDs_15_40_9"][-1]
        #log(f' MACD: {current_macd} - MH: {MH} - Signal: {macd_signal}')
        allocation_dict = {"USO": 0}  # Default to no allocation

        # Calculate the 200-day Bollinger Bands with 1.2 standard deviations
        bb = BB("USO", data, 200, 1.2)
        # Calculate the 50-day RSI
        rsi = RSI("USO", data, 50)
        # Calculate the 30-day and 15-day SMA
        sma30 = SMA("USO", data, 30)
        sma15 = SMA("USO", data, 15)
        
        if not bb or not rsi or not sma30 or not sma15:
            return TargetAllocation(allocation_dict)  # Return no allocation if any calculation failed

        # Check if current close price is above the upper Bollinger band, RSI > 50, and close > 30-day SMA
        if current_price > bb['upper'][-1] and rsi[-1] > 50 and current_price > sma30[-1]:
            allocation_dict["USO"] = 1  # Full allocation to USO
            allocation_dict["SCO"] = 0  # Close position
        elif current_price < bb['lower'][-1] and rsi[-1] < 42 and current_price < sma15[-1]:
            allocation_dict["USO"] = 0  # Close position
            allocation_dict["SCO"] = 0  # Close position
        # Check if the position should be closed - close is below the 15-day SMA or RSI < 50
        elif current_price < bb['upper'][-1] or rsi[-1] < 52 or current_price > sma15[-1]:
            allocation_dict["USO"] = 0  # Close position
            allocation_dict["SCO"] = 0  # Close position
        
        return TargetAllocation(allocation_dict)