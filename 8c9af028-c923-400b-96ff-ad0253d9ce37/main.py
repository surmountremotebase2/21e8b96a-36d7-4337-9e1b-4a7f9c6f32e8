from surmount.base_class import Strategy, TargetAllocation, backtest
from surmount.logging import log
from datetime import datetime

class TradingStrategy(Strategy):

   def __init__(self):
      self.tickers = ["NVDA", "GOOGL", "MSFT", "AMZN", "TSLA", "IBM", "INTC", "BIDU", "AMD", "CRM", "NOW", "TWLO", "PATH", "CGNX", "MU", "ASML", "DOCU", "CRWD", "OKTA", "PLTR", "ZS", "FSLY", "SNOW", "DDOG", "SNPS", "CDNS", "ANSS", "ADSK", "NTNX", "APPN", "ANET", "TDC", "PEGA", "VRNS", "AI", "ESTC", "TENB"]
      self.weights = [0.06, 0.06, 0.06, 0.06, 0.06, 0.04, 0.04, 0.03, 0.04, 0.02, 0.02, 0.02, 0.03, 0.02, 0.02, 0.04, 0.02, 0.03, 0.02, 0.01, 0.01, 0.02, 0.02, 0.03, 0.01, 0.01, 0.01, 0.01, 0.02, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.06]
      self.equal_weighting = False
      self.count = 0

   @property
   def interval(self):
      return "1day"

   @property
   def assets(self):
      return self.tickers

   def run(self, data):
      if len(data['ohlcv']) < 2:
          self.count += 1
          if self.count >= 30:
              self.count = 0
              if self.equal_weighting: 
                allocation_dict = {i: 1/len(self.tickers) for i in self.tickers}
              else:
                allocation_dict = {self.tickers[i]: self.weights[i] for i in range(len(self.tickers))} 
              return TargetAllocation(allocation_dict)
          else:
              return None

      today = datetime.strptime(str(next(iter(data['ohlcv'][-1].values()))['date']), '%Y-%m-%d %H:%M:%S')
      yesterday = datetime.strptime(str(next(iter(data['ohlcv'][-2].values()))['date']), '%Y-%m-%d %H:%M:%S')
      
      if today.day == 11 or (today.day > 11 and yesterday.day < 11):
         if self.equal_weighting: 
            allocation_dict = {i: 1/len(self.tickers) for i in self.tickers}
         else:
            allocation_dict = {self.tickers[i]: self.weights[i] for i in range(len(self.tickers))} 
         return TargetAllocation(allocation_dict)
      return None