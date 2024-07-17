from surmount.base_class import Strategy, TargetAllocation
from surmount.data import Asset
from surmount.technical_indicators import SMA

class TradingStrategy(Strategy):
    def __init__(self):
        # Defining the tickers of interest
        self.tickers = ["SPY", "TLT"]
        # Defining the data_list to fetch historical high and low prices for calculating moving averages
        self.data_list = [Asset(i) for i in self.tickers]
        # To keep track of the days since entered the position
        self.days_since_position = 0
        # To store if we have entered a position
        self.in_position = False

    @property
    def interval(self):
        # Using daily data for the calculations
        return "1day"

    @property
    def assets(self):
        return self.tickers

    @property
    def data(self):
        return self.data_list

    def run(self, data):
        allocation_dict = {"SPY": 0, "TLT": 0}  # Default to no allocation

        if self.days_since_position < 10 and self.in_position:
            # Increment the counter and maintain the positions as they are
            self.days_since_position += 1
        elif self.days_since_position == 10:
            # Close positions by reversing allocations
            allocation_dict = {"SPY": 0, "TLT": 0}  # Close both positions
            self.in_position = False  # Reset the in_position flag
            self.days_since_position = 0  # Reset the counter
        else:
            # Calculate the 50-day SMA of the H-L difference for both SPY and TLT
            ohlcv_data_spy = data["ohlcv"]["SPY"]
            ohlcv_data_tlt = data["ohlcv"]["TLT"]

            if len(ohlcv_data_spy) > 50 and len(ohlcv_data_tlt) > 50:  # Ensure there's enough data
                h_l_spy = [day["high"] - day["low"] for day in ohlcv_data_spy[-51:]]  # Last 51 days (including today)
                h_l_tlt = [day["high"] - day["low"] for day in ohlcv_data_tlt[-51:]]

                avg_h_l_spy = sum(h_l_spy[:-1]) / 50  # Exclude today for calculation
                avg_h_l_tlt = sum(h_l_tlt[:-1]) / 50

                todays_change_spy = ohlcv_data_spy[-1]["close"] - ohlcv_data_spy[-2]["close"]
                todays_change_tlt = ohlcv_data_tlt[-1]["close"] - ohlcv_data_tlt[-2]["close"]

                condition_spy = todays_change_spy <= -1.25 * avg_h_l_spy
                condition_tlt = todays_change_tlt >= 1.25 * avg_h_l_tlt

                if condition_spy and condition_tlt:
                    allocation_dict = {"SPY": 1, "TLT": 0}  # Go long SPY and short TLT
                    self.in_position = True  # Mark that we've entered a position
                    self.days_since_position += 1  # Start counting the days

        return TargetAllocation(allocation_dict)



        