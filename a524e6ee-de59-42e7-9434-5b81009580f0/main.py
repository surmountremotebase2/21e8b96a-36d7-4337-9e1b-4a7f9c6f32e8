from surmount.base_class import Strategy, TargetAllocation
import pandas as pd

class TradingStrategy(Strategy):
    def __init__(self):
        # Define the global asset classes and the crash protection asset
        self.asset_classes = ["Asset1", "Asset2", "Asset3", "Asset4", "Asset5", 
                              "Asset6", "Asset7", "Asset8", "Asset9", "Asset10",
                              "Asset11", "Asset12"]
        self.crash_protection_asset = "CPAsset"
        self.interval = "1month"

    @property
    def assets(self):
        # Include the crash protection asset in the list
        return self.asset_classes + [self.crash_protection_asset]

    def run(self, data):
        allocations = {}
        momentum_scores = self.calculate_momentum_scores(data)

        # Calculate number of assets with positive momentum
        positive_momentum_assets = sum(m > 0 for m in momentum_scores.values())

        # Determine the allocation to crash protection asset
        if positive_momentum_assets <= 6:
            # Allocate everything to crash protection asset if 6 or fewer assets have positive momentum
            allocations[self.crash_protection_asset] = 1.0
            for asset in self.asset_classes:
                allocations[asset] = 0.0
        else:
            cp_allocation = (12 - positive_momentum_assets) / 6
            allocations[self.crash_protection_asset] = cp_allocation
            
            # Determine allocations for assets with positive momentum
            sorted_assets_by_momentum = sorted(momentum_scores, key=momentum_scores.get, reverse=True)[:6]
            for asset in self.asset_classes:
                if asset in sorted_assets_by_momentum:
                    allocations[asset] = (1 - cp_allocation) / 6
                else:
                    allocations[asset] = 0.0

        return TargetAllocation(allocations)

    def calculate_momentum_scores(self, data):
        """
        Calculate momentum scores for asset classes based on the formula:
        MOMt = [(closet / SMA(t..t-12)) – 1]
        """
        momentum_scores = {}
        for asset in self.asset_classes:
            close_data = data["ohlcv"][-1][asset]['close']
            sma = self.calculate_sma(asset, data["ohlcv"])
            if sma > 0:  # Avoid division by zero
                momentum_score = (close_data / sma) - 1
            else:
                momentum_score = 0
            momentum_scores[asset] = momentum_score
        return momentum_scores

    def calculate_sma(self, asset, data):
        """
        Calculate Simple Moving Average (SMA) for an asset over the last 13 months.
        """
        close_prices = [x[asset]['close'] for x in data[-13:]]
        if len(close prices) == 13:
            return sum(close_prices) / len(close_prices)
        return 0

# Note: This code assumes the presence of an underlying function or mechanism within the Surmount AI framework
# that fetches the necessary historical data (monthly close prices for the past 13 months for each asset class)
# and calls