from surmount.base_class import Strategy, TargetAllocation, backtest
from surmount.technical_indicators import MACD, RSI, EMA
from surmount.logging import log
import pandas as pd
from datetime import date, time, datetime, timedelta


class TradingStrategy(Strategy):
    def __init__(self):
        # Define the global asset classes and the crash protection asset
        #self.tickers = ["SPY", "QQQ", "TECL", "IWM", "VGK", 
        #self.tickers = ["SPY", "QQQ", "TECL", "DBC",
        #                      #"EWJ", "EEM", "XLK", "HYG", "XLU", "XLV", "LQD",
        #                      "XLK", "XLV", "XLE", "FEZ", "STIP", "TLT", "IEF", "EWJ", "GLD",
        #                      "MTUM", "SPLV", "SOXX"]
        self.tickers = ["QQQ", "TECL", "DBC", "XLV", "XLE", "TLT", "IEF", "TIP", "GLD", "XLK", "SOXX"]
        self.crash_protection_asset1 = "TIP"
        self.crash_protection_asset2 = "SHV"
        self.SafeAssets = ["IEF", "TLT", "GLD", "TIP", "DBC"]
        self.cplist = [self.crash_protection_asset2, "XLI", "XLU"]
        self.RiskON = 2  #Number of Risk ON Assets
        self.RiskOFF = 2 #Number of Risk OFF Assets
        self.LTMA = 100  #Long Term Moving Average
        self.STMOM = 20   #Short Term Momentum
        self.LTMOM = 128   #Short Term Momentum
        self.STMA = 20
        self.DAYOFWEEK = 4
        self.init = 0
        self.last_allocations = {}

    @property
    def interval(self):
        return "1day"


    @property
    def assets(self):
        # Include the crash protection asset in the list
        return self.tickers + self.cplist

    def run(self, data):
        allocations = {}
        is_last_day = False
        today = date.today() #GET Today's date
        datatick = data["ohlcv"]
        today = datatick[-1]["QQQ"]["date"]
        # Convert the strings to datetime objects using to_datetime
        today = pd.to_datetime(today)
        dayweek = today.weekday()
        #log(f"WeekDay: {str(dayweek)}")
        # Check if tomorrow belongs to the same month as today
        is_last_day = today.month != (today + timedelta(days=2)).month
        if dayweek == self.DAYOFWEEK:
            is_last_day = True

        if is_last_day or self.init == 0:
            self.init = 1

        momentum_scores = self.calculate_momentum_scores(data)
        ema = EMA("QQQ", datatick, self.STMA)[-1]
        xlu = (datatick[-1]["XLU"]["close"] - datatick[-45]["XLU"]["close"]) / datatick[-45]["XLU"]["close"]
        xli = (datatick[-1]["XLI"]["close"] - datatick[-45]["XLI"]["close"]) / datatick[-45]["XLI"]["close"]
        #log(f"{macd_signal}")
        mrktclose = datatick[-1]["QQQ"]["close"]
        teclmrktclose = datatick[-1]["TECL"]["close"]
        mrktrsi = RSI("QQQ", datatick, 15)[-1]
        mrktema = EMA("QQQ", datatick, 5)[-1]

        
        # Log the allocation for the current run.
        
        #log(f"NUM POS MOM {today.strftime('%Y-%m-%d')}: {positive_momentum_assets}")
        #positive_momentum_assets = 3
        # Determine allocations for assets with positive momentum
        if mrktclose < mrktema and mrktrsi < 70 and mrktrsi > 30:
            del momentum_scores["TECL"]
        
        # Calculate number of assets with positive momentum
        positive_momentum_assets = sum(m > 0 for m in momentum_scores.values())

        sorted_assets_by_momentum = sorted(momentum_scores, key=momentum_scores.get, reverse=True)[:self.RiskON]
        TopMom = sorted_assets_by_momentum[0]
        #log(f"TopMom: {TopMom}")

        # Determine the allocation to crash protection asset
        if (positive_momentum_assets <= 2) or (xlu > xli and TopMom in self.SafeAssets):
            #log(f"RISK OFF: SHV")
            # Allocate everything to crash protection asset if 6 or fewer assets have positive momentum
            #cpmomentum_scores = self.calculate_cpmomentum_scores(data)
            #sorted_cpassets_by_momentum = sorted(cpmomentum_scores, key=momentum_scores.get, reverse=True)
            # Calculate number of assets with positive momentum
            #allocations[self.crash_protection_asset1] = 0.3
            for asset in self.tickers:
                allocations[asset] = 0.0            
            if TopMom in self.SafeAssets:
                allocations[TopMom] = 0.5
                allocations[self.crash_protection_asset2] = 0.5
            else:
                allocations[self.crash_protection_asset2] = 1.0

        else:
            
            cp_allocation = 0.0
            allocations[self.crash_protection_asset2] = cp_allocation

            #log(f"Sorted MOM {today.strftime('%Y-%m-%d')}: {sorted_assets_by_momentum}")
            for asset in self.tickers:
                if asset in sorted_assets_by_momentum:
                    #allocations[asset] = (1 - cp_allocation) / positive_momentum_assets
                    allocations[asset] = float(1 / self.RiskON)
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
            ema = technical_indicators.MFI(asset, data, self.STMA)
            #close_prices = pd.DataFrame(close_prices)
            sma = self.calculate_sma(asset, datatick)
            if sma > 0:  # Avoid division by zero
                momentum_score = (close_data / sma) - 1
                #momentum_score = ( ((close_data / sma) *2) - (close_data / close_prices[-self.STMOM]) ) -1
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
            close_prices = [x[asset]['close'] for x in datatick[-self.LTMOM:]]
            #close_prices = pd.DataFrame(close_prices)
            sma = self.calculate_sma(asset, data["ohlcv"])
            ema = EMA(asset, datatick, self.STMA)[-1]
            if sma > 0:  # Avoid division by zero
                #momentum_score = ( ((close_data / sma) *2) - ((close_data / close_prices[-self.STMOM])) ) -1
                momentum_score = ( (close_data / sma) - 1 )
            else:
                momentum_score = 0.0
            if ema > 0:
                momentum_score = momentum_score + ( (close_data / ema) - 1 )
            momentum_scores[asset] = momentum_score
        return momentum_scores

    def calculate_sma(self, asset, data):
        """
        Calculate Simple Moving Average (SMA) for an asset over the last 13 months.
        """
        close_prices = [x[asset]['close'] for x in data[-self.LTMA:]]
        sma = pd.DataFrame(close_prices).mean()
        if sma[0] == 0:
            return 0.0
        else:
            return sma[0]

    def calculate_shortsma(self, asset, data):
        """
        Calculate Simple Moving Average (SMA) for an asset over the last 13 months.
        """
        close_prices = [x[asset]['close'] for x in data[-self.STMA:]]
        sma = pd.DataFrame(close_prices).mean()
        if sma[0] == 0:
            return 0.0
        else:
            return sma[0]