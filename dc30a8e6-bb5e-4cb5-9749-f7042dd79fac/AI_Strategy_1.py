from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import EMA, RSI
from surmount.data import ohlcv
import pandas as pd
import pandas_ta as ta

class TradingStrategy(Strategy):
    def __init__(self):
        self.tickers = ["SPY"]

    @property
    def interval(self):
        return "1day"

    @property
    def assets(self):
        return self.tickers

    def KeltnerChannel(self, ticker, data, length=30):
        """
        Computes the Keltner Channel for the given ticker and data.
        
        :param ticker: Ticker symbol as a string
        :param data: List[Dict[str, Dict[str, float]]] containing the OHLCV data
        :param length: The lookback period for the channel
        :return: A dictionary containing the upper, middle, and lower bands of the Keltner Channel
        """
        high_prices = pd.Series([x[ticker]["high"] for x in data])
        low_prices = pd.Series([x[ticker]["low"] for x in data])
        close_prices = pd.Series([x[ticker]["close"] for x in data])
        # Middle line is the Exponential Moving Average (EMA) of closing prices
        middle = ta.ema(close_prices, length=length)
        # Range is the difference between the high and low prices
        range = high_prices - low_prices
        # The average true range (ATR) as the range component of the channel
        atr = ta.atr(high_prices, low_prices, close_prices, length=length)
        upper = middle + (2 * atr)
        lower = middle - (2 * atr)
        
        return {"upper": upper, "middle": middle, "lower": lower}

    def run(self, data):
        # Fetch data for SPY
        spy_data = data["ohlcv"]
        # Calculate Keltner Channel
        kc = self.KeltnerChannel("SPY", spy_data)
        # Calculate 7-day EMA for SPY
        spy_ema7 = EMA("SPY", spy_data, 7)
        spy_rsi = RSI("SPY", spy_data, 5)
        
        # Check if enough data available to make a decision
        if kc["middle"] is None or kc["upper"] is None or len(spy_ema7) < 2:
            return TargetAllocation({})
        
        # Current and previous 7-day EMA values
        ema7_today = spy_ema7[-1]
        ema7_prev = spy_ema7[-2]
        
        # Current Keltner middle band
        middle_band_today = kc["middle"][-1]
        # Previous Keltner middle band
        middle_band_prev = kc["middle"][-2]
        
        # Upper Keltner band
        upper_band_today = kc["upper"][-1]
        
        # BUY logic: EMA crosses above the middle band
        if ema7_today > middle_band_today and ema7_prev < middle_band_prev and spi_rsi:
            # Allocate 100% of the portfolio to SPY
            allocation = {"SPY": 1.0}
        # SELL logic: EMA crosses below the upper band
        elif ema7_today < upper_band_today and ema7_prev > upper_band_today:
            # Liquidate SPY from the portfolio
            allocation = {"SPY": 0}
        else:
            # Maintain existing allocation if no conditions are met
            allocation = {}
        
        return TargetAllocation(allocation)