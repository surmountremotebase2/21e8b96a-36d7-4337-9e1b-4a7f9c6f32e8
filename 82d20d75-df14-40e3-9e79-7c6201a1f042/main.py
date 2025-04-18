from surmount.base_class import Strategy, TargetAllocation
from surmount.data import Asset
from surmount.technical_indicators import SMA
from surmount.logging import log
import pandas as pd

class TradingStrategy(Strategy):
    def __init__(self):
        # Defining the tickers of interest
        self.tickers = ["SPY", "TLT"]
        # Defining the data_list to fetch historical high and low prices for calculating moving averages
        self.data_list = self.tickers
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

    def run(self, data):
        allocation_dict = {"SPY": 1, "TLT": 0}  # Default to no allocation

        return TargetAllocation(allocation_dict)