from surmount.base_class import Strategy, TargetAllocation, backtest
from surmount.technical_indicators import MACD, RSI, EMA
from surmount.logging import log
import pandas as pd
import numpy as np
from datetime import date, time, datetime, timedelta


class TradingStrategy(Strategy):
    def __init__(self):
        # Define the global asset classes and the crash protection asset
        #self.tickers = ["QQQ", "XLV", "DBC", "TQQQ", "SPY", "TECL", "XLK", "SOXX", "IJT"]
        self.tickers = ["QQQ", "DBC", "TECL", "XLK", "SOXX", "IJT"]
        self.SafeAssets = ["IEF", "TLT", "BIL", "TIP", "XLV", "GLD"]
        self.Canary = ["SLV", "XLI", "XLU", "UUP", "DBB"]
        self.RiskAsset = "QQQ"
        self.SafeAsset = "BIL"

        self.INIT_WAITD = 15
        self.VOLA_LOOKBACK = 126
        self.LOOKD_CONST = 83
        self.EXCL_D = 21
        self.RiskFlag = False
        self.bull = True
        self.count = 0
        self.outday = 0

        self.RiskON = 3  #Number of Risk ON Assets
        self.RiskOFF = 2 #Number of Risk OFF Assets
        self.LTMA = 100  #Long Term Moving Average
        self.STMOM = 20   #Short Term Momentum
        self.LTMOM = 252   #Short Term Momentum
        self.VolaThreashold = .21
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
        return self.tickers + self.SafeAssets + self.Canary

    def run(self, data):
        allocations = {}
        DATA = {}

        today = date.today() #GET Today's date
        datatick = data["ohlcv"]
        today = datatick[-1]["QQQ"]["date"]
        # Convert the strings to datetime objects using to_datetime
        today = pd.to_datetime(today)
        dayweek = today.weekday()

        #dataDF = pd.DataFrame()
        #log(f'{datatick.iloc[-1]}')

        QQQClose = [x['QQQ']['close'] for x in datatick[-self.LTMOM:]]
        #SPYClose = [x['SPY']['close'] for x in datatick[-self.LTMOM:]]
        DATA['XLU'] = [x['XLU']['close'] for x in datatick[-self.LTMOM:]]
        DATA['XLI'] = [x['XLI']['close'] for x in datatick[-self.LTMOM:]]
        DATA['GLD'] = [x['GLD']['close'] for x in datatick[-self.LTMOM:]]
        DATA['SLV'] = [x['SLV']['close'] for x in datatick[-self.LTMOM:]]
        DATA['UUP'] = [x['UUP']['close'] for x in datatick[-self.LTMOM:]]
        DATA['DBB'] = [x['DBB']['close'] for x in datatick[-self.LTMOM:]]
        #log(f'{close_prices}')
        dates = [x['QQQ']['date'] for x in datatick[-self.LTMOM:]]
        dates = pd.to_datetime(dates)
        dataDFQQQ = pd.DataFrame(QQQClose, columns=['close'], index=dates)
        #dataDFSPY = pd.DataFrame(SPYClose, columns=['close'], index=dates)
        dataDF = pd.DataFrame(DATA, columns=['XLU', 'XLI', 'GLD', 'SLV', 'UUP', 'DBB'], index=dates)
        dataDFQQQ['QQQ_Returns'] = dataDFQQQ['close'].pct_change()
        #dataDFSPY['SPY_Returns'] = dataDFSPY['close'].pct_change()

        # Calculate the standard deviation of daily returns (daily volatility)
        daily_volatility = dataDFQQQ['QQQ_Returns'].std()
        #daily_volatility = dataDFSPY['SPY_Returns'].std()
        QQQVola = daily_volatility * np.sqrt(252)
        WAITDays = int(QQQVola * self.LOOKD_CONST * .8)
        #RETLookback = int((1.0 - QQQVola) * self.LOOKD_CONST)
        RETLookback = int((1.0 - QQQVola) * self.LOOKD_CONST)
        #log(f'{QQQVola}')

        xluret = dataDF["XLU"].pct_change(RETLookback).iloc[-1]
        xliret = dataDF["XLI"].pct_change(RETLookback).iloc[-1]
        gldret = dataDF["GLD"].pct_change(RETLookback).iloc[-1]
        slvret = dataDF["SLV"].pct_change(RETLookback).iloc[-1]
        uupret = dataDF["UUP"].pct_change(RETLookback).iloc[-1]
        dbbret = dataDF["DBB"].pct_change(RETLookback).iloc[-1]

        self.RiskFlag = ( (gldret > slvret) and (xluret > xliret) and (uupret > dbbret) )

        #log(f"{macd_signal}")
        mrktclose = datatick[-1]["QQQ"]["close"]
        
        if self.RiskFlag:
            self.bull = False
            self.outday = self.count
        if self.count >= (self.outday + WAITDays):
            self.bull = True
        self.count += 1

        if self.bull:
            momentum_scores = self.calculate_momentum_scores(data)

            positive_momentum_assets = sum(m > 0 for m in momentum_scores.values())
            sorted_assets_by_momentum = sorted(momentum_scores, key=momentum_scores.get, reverse=True)
            if QQQVola > self.VolaThreashold:
                sorted_assets_by_momentum.remove('TECL')
            if len(sorted_assets_by_momentum) > 0 and positive_momentum_assets > 0:
                TopMom = sorted_assets_by_momentum[0]
            else:
                TopMom = 'XLV'
            self.RiskAsset = TopMom

            allocations[self.SafeAsset] = 0
            allocations[self.RiskAsset] = 1.0
        else:
            safe_scores = self.calculate_safe_scores(data)

            sorted_safe_by_momentum = sorted(safe_scores, key=safe_scores.get, reverse=True)
            if len(sorted_safe_by_momentum) > 0:
                TopSafeMom = sorted_safe_by_momentum[0]
            else:
                TopSafeMom = 'BIL'
            self.SafeAsset = TopSafeMom

            allocations[self.SafeAsset] = 1.0
            allocations[self.RiskAsset] = 0

        return TargetAllocation(allocations)

    def calculate_momentum_scores(self, data):
        """
        Calculate momentum scores for asset classes based on the formula:
        MOMt = [(closet / SMA(t..t-12)) – 1]
        """
        momentum_scores = {}
        datatick = data["ohlcv"]
        for asset in self.tickers:
            close_data = data["ohlcv"][-1][asset]['close']
            close_prices = [x[asset]['close'] for x in datatick[-self.VOLA_LOOKBACK:]]
            #close_prices = pd.DataFrame(close_prices)
            sma = self.calculate_sma(asset, data["ohlcv"])
            ema = EMA(asset, datatick, 15)[-1]
            #ema = 0
            if sma > 0:  # Avoid division by zero
                #momentum_score = ( (((close_data / sma)) -1) + ((close_data - close_prices[-self.STMOM]) / close_prices[-self.STMOM]) *2 )
                momentum_score = ( (close_data / sma) - 1 ) - ( (close_data / ema) - 1 )
            else:
                momentum_score = 0.0

            momentum_scores[asset] = momentum_score
        return momentum_scores

    def calculate_safe_scores(self, data):
        """
        Calculate momentum scores for asset classes based on the formula:
        MOMt = [(closet / SMA(t..t-12)) – 1]
        """
        momentum_scores = {}
        datatick = data["ohlcv"]
        for asset in self.SafeAssets:
            close_data = data["ohlcv"][-1][asset]['close']
            close_prices = [x[asset]['close'] for x in datatick[-self.VOLA_LOOKBACK:]]
            #close_prices = pd.DataFrame(close_prices)
            sma = self.calculate_sma(asset, data["ohlcv"])
            ema = EMA(asset, datatick, 15)[-1]
            #ema = 0
            if sma > 0:  # Avoid division by zero
                #momentum_score = ( (((close_data / sma)) -1) + ((close_data - close_prices[-self.STMOM]) / close_prices[-self.STMOM]) *2 )
                momentum_score = ( (close_data / sma) - 1 ) - ( (close_data / ema) - 1 )
            else:
                momentum_score = 0.0

            momentum_scores[asset] = momentum_score
        return momentum_scores

    def calculate_sma(self, asset, data):
        """
        Calculate Simple Moving Average (SMA) for an asset over the last 13 months.
        """
        close_prices = [x[asset]['close'] for x in data[-self.LOOKD_CONST:]]
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