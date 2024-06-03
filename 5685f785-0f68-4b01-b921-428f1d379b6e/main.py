from surmount.base_class import Strategy, TargetAllocation
from surmount.logging import log
from datetime import datetime

class TradingStrategy(Strategy):
    def __init__(self):
        # Define the tickers to be used in this strategy.
        self.tickers = ["SPY", "TLT"]
        self.data_list = []  # This strategy does not require extra data inputs.

    @property
    def interval(self):
        # The trading interval is set to '1day' to match our monthly trading criterion.
        return "1day"

    @property
    def assets(self):
        # Return the list of asset tickers this strategy interacts with.
        return self.tickers

    @property
    def data(self):
        # Return required data. For this strategy, an empty list suffices.
        return self.data_list

    def run(self, data):
        # Initialize the target allocation for each ticker to 0.
        allocation_dict = {ticker: 0 for ticker in self.tickers}

        # Get today's date.
        today = datetime.now()
        # Check if today is the first day of the month to buy SPY.
        if today.day == 1:
            allocation_dict["SPY"] = 1.0
        # Check if today is the last day of the month to buy TLT.
        # This check involves seeing if tomorrow's day is less than today's,
        # which would imply today is the last day of the month.
        tomorrow = today.replace(day=today.day % 28 + 1)  # Handles most month lengths properly.
        if tomorrow.day < today.day:
            allocation_dict["TLT"] = 1.0

        # Log the allocation for the current run.
        log(f"Trading allocations for {today.strftime('%Y-%m-%d')}: {allocation_dict}")

        # Return the calculated allocations wrapped in a TargetAllocation object.
        return TargetAllocation(allocation_dict)