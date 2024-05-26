from surmount.base_class import Strategy, TargetAllocation
# Make sure to import other necessary modules or classes as needed

class TradingStrategy(Strategy):
    def __init__(self):
        # Initialization of your strategy. Define the assets you are interested in.
        self.tickers = ["AAPL", "MSFT"]  # Example tickers
        # You can also initialize other variables or data sources here.

    @property
    def assets(self):
        # Return a list of asset tickers that the strategy will operate on.
        return self.tickers

    @property
    def interval(self):
        # Define the data interval for the strategy.
        # It should match the intervals provided by the data source.
        # Common intervals include "1day", "1hour", "15min", etc.
        return "1day"  # For daily data

    def run(self, data):
        # Implement your trading logic here. The 'data' parameter will contain
        # market data and other relevant information as defined in your strategy.

        # Example strategy: equally split allocation between tickers
        allocation_dict = {ticker: 1.0 / len(self.tickers) for ticker in self.tickers}

        # Return the target allocation based on your logic
        return TargetAllocation(allocation_dict)