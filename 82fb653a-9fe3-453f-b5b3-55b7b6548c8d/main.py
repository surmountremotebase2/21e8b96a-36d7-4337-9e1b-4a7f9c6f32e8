from surmount.base_class import Strategy, TargetAllocation
from surmount.data import Asset
from surmount.logging import log
import pandas as pd

class TradingStrategy(Strategy):
    def __init__(self):
        # Define the asset for the strategy and initial target allocation
        self.tickers = ["SPY", "TQQQ"]
        self.hold_days = 0 # Counter to keep track of holding duration
        self.buy_signal = False # Flag to indicate a buy signal from the strategy

    @property
    def interval(self):
        # We set the interval to "1day" to assess the daily prices
        return "1day"

    @property
    def assets(self):
        # Assets involved in the trading strategy
        return self.tickers

    @property
    def data(self):
        # No additional data sources required beyond default OHLCV data
        return []

    def IBS(self, close, high, low):
        """Internal Bar Strength (IBS) calculation.
        
        Parameters:
        - close: The closing price
        - high: The high price of the day
        - low: The low price of the day
        
        Returns:
        - IBS value as a float
        """
        return (close - low) / (high - low) if (high - low) > 0 else 0

    def run(self, data):
        # Initialize TQQQ allocation to 0
        allocation = {"TQQQ": 0}

        StockData = data["ohlcv"]
        #d[-1]["QQQ"]
        # Retrieve OHLCV data for SPY
        StockDF = pd.DataFrame(StockData)

        ohlcv_tqqq = StockDF["TQQQ"]
        
        # Ensure we have at least two days of data for SPY to compare
        if len(ohlcv_spy) >= 2:
            # Define "yesterday" and "today" based on the latest two data points
            yesterday = ohlcv_spy[-2]
            today = ohlcv_spy[-1]

            # Check if today is a Monday and if the conditions are fulfilled
            today_date = pd.to_datetime(today['date'])
            if today_date.weekday() == 0:  # 0 represents Monday
                ibs_today = self.IBS(today['close'], today['high'], today['low'])
                if today['close'] < yesterday['close'] and ibs_today < 0.5:
                    # Mark buy signal as True if conditions are met
                    self.buy_signal = True
            
            # Sell conditions based on SPY performance or holding duration
            if self.buy_signal:
                if self.hold_days >= 4 or today['close'] > yesterday['high']:
                    # Sell TQQQ (set allocation to 0) if holding period is 4 days or SPY closes higher than yesterday's high
                    self.buy_signal = False  # Reset buy signal
                    self.hold_days = 0  # Reset holding counter
                else:
                    # Keep holding TQQQ
                    allocation["TQQQ"] = 1
                    self.hold_days += 1
        
        if self.buy_signal and self.hold_days == 0:
            # If a buy signal was triggered and we are in the initial day of action
            allocation["TQQQ"] = 1
            self.hold_days = 1  # Increment the hold day counter since we decided to buy

        # Log the action for diagnostic purposes
        log(f'Day {self.hold_days} of holding TQQQ with allocation: {allocation["TQQQ"]}')

        return TargetAllocation(allocation)