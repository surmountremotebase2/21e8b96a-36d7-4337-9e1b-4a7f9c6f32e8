from surmount.base_class import Strategy, TargetAllocation, backtest
from surmount.technical_indicators import MACD, RSI, EMA
from surmount.logging import log
import pandas as pd
import numpy as np
from datetime import date, time, datetime, timedelta


class TradingStrategy(Strategy):
    def __init__(self):
        # Define the global asset classes and the crash protection asset
        self.tickers = ["QQQ", "XLV", "DBC", "TQQQ", "SPY", "TECL", "XLK", "SOXX", "IJT"]
        self.SafeAssets = ["IEF", "TLT", "BIL"]
        self.Canary = ["GLD", "SLV", "XLI", "XLU", "UUP", "DBB"]
        self.RiskAsset = "TQQQ"
        self.SafeAsset = "BIL"

        self.INIT_WAITD = 15
        self.VOLA_LOOKBACK = 126
        self.LOOKD_CONST = 83
        self.EXCL_D = 21
        self.RiskFlag = False
        self.bull = True
        self.count = 0

        self.RiskON = 3  #Number of Risk ON Assets
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
        return self.tickers + self.SafeAssets + self.Canary

    def run(self, data):
        allocations = {}

        today = date.today() #GET Today's date
        datatick = data["ohlcv"]
        today = datatick[-1]["QQQ"]["date"]
        # Convert the strings to datetime objects using to_datetime
        today = pd.to_datetime(today)
        dayweek = today.weekday()

        dataDF = pd.DataFrame(datatick)
        #log(f'{datatick.iloc[-1]}')
        
        dataDFQQQ = pd.DataFrame([data['QQQ']])
        log(f'{dataDFQQQ.iloc[-1]}')
        dataDFQQQ['date'] = pd.to_datetime(dataDFQQQ['date'])
        dataDFQQQ.set_index('date', inplace=True)
        log(f'{dataDFQQQ.iloc[-1]}')

        dataDFQQQ['QQQ_Returns'] = dataDFQQQ.pct_change()
        # Calculate the standard deviation of daily returns (daily volatility)
        daily_volatility = dataDFQQQ['QQQ_Returns'].std()
        QQQVola = daily_volatility * np.sqrt(252)
        WAITDays = int(QQQVola * self.LOOKD_CONST)
        RETLookback = int((1.0 - QQQVola) * self.LOOKD_CONST)

        xluret = dataDF["XLU"].loc['close'].pct_change(RETLookback).iloc[-1]
        xliret = dataDF["XLI"].loc['close'].pct_change(RETLookback).iloc[-1]
        gldret = dataDF["GLD"].loc['close'].pct_change(RETLookback).iloc[-1]
        slvret = dataDF["SLV"].loc['close'].pct_change(RETLookback).iloc[-1]
        uupret = dataDF["UUP"].loc['close'].pct_change(RETLookback).iloc[-1]
        dbbret = dataDF["DBB"].loc['close'].pct_change(RETLookback).iloc[-1]

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
            allocations[self.SafeAsset] = 0
            allocations[self.RiskAsset] = 1.0
        else:
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
            close_prices = [x[asset]['close'] for x in datatick[-self.LTMOM:]]
            #close_prices = pd.DataFrame(close_prices)
            sma = self.calculate_sma(asset, data["ohlcv"])
            ema = EMA(asset, datatick, 15)[-1]
            #ema = 0
            if sma > 0:  # Avoid division by zero
                momentum_score = ( (((close_data / sma)) -1) + ((close_data - close_prices[-self.STMOM]) / close_prices[-self.STMOM]) *2 )
                #momentum_score = ( (close_data / sma) - 1 )
            else:
                momentum_score = 0.0
            if ema > 0:
                momentum_score = momentum_score + ( (close_data - ema) / ema) 
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