from surmount.base_class import Strategy, TargetAllocation, backtest
from surmount.logging import log
import pandas as pd



class TradingStrategy(Strategy):
    def __init__(self):
        # Define the global asset classes and the crash protection asset
        #self.tickers = ["SPY", "QQQ", "TECL", "IWM", "VGK", 
        self.tickers = ["SPY", "QQQ", "TECL", "IWM", "IJT", 
                              #"EWJ", "EEM", "XLK", "HYG", "XLU", "XLV", "LQD",
                              "EWJ", "EEM", "XLK", "XLU", "XLV", "SH", 
                              "SPLV", "MTUM", "DBC", "SOXX"]
        self.crash_protection_asset1 = "TIP"
        self.crash_protection_asset2 = "BIL"
        self.cplist = [self.crash_protection_asset1, self.crash_protection_asset2]
        self.RiskON = 3  #Number of Risk ON Assets
        self.RiskOFF = 2 #Number of Risk OFF Assets
        self.LTMA = 100  #Long Term Moving Average
        self.STMOM = 20   #Short Term Momentum
        self.LTMOM = 128   #Short Term Momentum

    @property
    def interval(self):
        return "1day"


    @property
    def assets(self):
        # Include the crash protection asset in the list
        return self.tickers + self.cplist

    def run(self, data):
        allocations = {}
        momentum_scores = self.calculate_momentum_scores(data)

        # Calculate number of assets with positive momentum
        positive_momentum_assets = sum(m >= 0 for m in momentum_scores.values())
        print(positive_momentum_assets)
        #positive_momentum_assets = 3

        # Determine the allocation to crash protection asset
        if positive_momentum_assets <= 1:
            # Allocate everything to crash protection asset if 6 or fewer assets have positive momentum
            #cpmomentum_scores = self.calculate_cpmomentum_scores(data)
            #sorted_cpassets_by_momentum = sorted(cpmomentum_scores, key=momentum_scores.get, reverse=True)
            # Calculate number of assets with positive momentum
            allocations[self.crash_protection_asset1] = 0.3
            allocations[self.crash_protection_asset2] = 0.7
            for asset in self.tickers:
                allocations[asset] = 0.0
        else:
            if positive_momentum_assets < self.RiskON:
                cp_allocation = (self.RiskON - positive_momentum_assets) * (1/self.RiskON)
                allocations[self.crash_protection_asset1] = cp_allocation
            else:
                cp_allocation = 0

            # Determine allocations for assets with positive momentum
            sorted_assets_by_momentum = sorted(momentum_scores, key=momentum_scores.get, reverse=True)[:self.RiskON]
            for asset in self.tickers:
                if asset in sorted_assets_by_momentum:
                    allocations[asset] = (1 - cp_allocation) / self.RiskON
                else:
                    allocations[asset] = 0.0

        return TargetAllocation(allocations)

    def calculate_cpmomentum_scores(self, data):
        """
        Calculate momentum scores for asset classes based on the formula:
        MOMt = [(closet / SMA(t..t-12)) – 1]
        """
        momentum_scores = {}
        datatick = data["ohlcv"]
        for asset in self.cplist:
            close_data = datatick[-1][asset]['close']
            close_prices = [x[asset]['close'] for x in datatick[-252:]]
            #close_prices = pd.DataFrame(close_prices)
            sma = self.calculate_sma(asset, datatick)
            if sma > 0:  # Avoid division by zero
                #momentum_score = (close_data / sma) - 1
                momentum_score = ( ((close_data / sma) *2) - (close_data / close_prices[-self.STMOM]) )
            else:
                momentum_score = 0
            momentum_scores[asset] = momentum_score
        return momentum_scores

    def calculate_momentum_scores(self, data):
        """
        Calculate momentum scores for asset classes based on the formula:
        MOMt = [(closet / SMA(t..t-12)) – 1]
        """
        momentum_scores = {}
        datatick = data["ohlcv"]
        for asset in self.tickers:
            close_data = data["ohlcv"][-1][asset]['close']
            close_prices = [x[asset]['close'] for x in datatick[-252:]]
            #close_prices = pd.DataFrame(close_prices)
            sma = self.calculate_sma(asset, data["ohlcv"])
            if sma > 0:  # Avoid division by zero
                momentum_score = ( ((close_data / sma) *2) - (close_data / close_prices[-self.STMOM]) )
            else:
                momentum_score = 0
            momentum_scores[asset] = momentum_score
        return momentum_scores

    def calculate_sma(self, asset, data):
        """
        Calculate Simple Moving Average (SMA) for an asset over the last 13 months.
        """
        close_prices = [x[asset]['close'] for x in data[-self.LTMA:]]
        sma = pd.DataFrame(close_prices).mean()
        if sma[0] == 0:
            return 0
        else:
            return sma[0]