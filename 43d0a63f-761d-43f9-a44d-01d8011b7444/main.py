from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import RSI, EMA, SMA
from surmount.logging import log

class TradingStrategy(Strategy):
    def __init__(self):
        # Only trading with "USO" ETF
        self.ticker = ["SPY", "QQQ", "BIL"]
        self.RiskOn = "QQQ"
        self.RiskOff = "BIL"
        self.count = 5

    @property
    def assets(self):
        # Defines the asset to trade
        return self.ticker

    @property
    def interval(self):
        # Sets the strategy to run on daily data
        return "1day"


    def realized_volatility_daily(self, series_log_return):
        """
        Get the daily realized volatility which is calculated as the square root
        of sum of squares of log returns within a specific window interval 
        """
        n = len(series_log_return)
        vola =  np.sqrt(np.sum(series_log_return**2)/(n - 1))
        return vola



    def run(self, data):
        allocation = {}
        self.count -= 1
        spy_data = [entry['QQQ']['close'] for entry in data['ohlcv'] if 'SPY' in entry]
        spy_dates = [entry['QQQ']['date'] for entry in data['ohlcv'] if 'SPY' in entry]
        spy_data = pd.DataFrame(spy_data, columns=['close'])
        spy_data['returns'] = 100 * spy_data.close.pct_change().dropna()
        # CALCULATE LOG RETURNS BASED ON ABOVE FORMULA
        spy_data['log_returns'] = np.log(spy_data.close/spy_data.close.shift(1))
        spy_data = spy_data.fillna(0)
        INTERVAL_WINDOW = 60
        n_future = 20


        if len(spy_data) > n_future:
            # GET BACKWARD LOOKING REALIZED VOLATILITY
            spy_data['vol_current'] = spy_data.log_returns.rolling(window=INTERVAL_WINDOW).apply(self.realized_volatility_daily)
            spy_data['vol_current'] = spy_data['vol_current'].bfill()
            # GET FORWARD LOOKING REALIZED VOLATILITY 
            spy_data['vol_future'] = spy_data.log_returns.shift(n_future).fillna(0).rolling(window=INTERVAL_WINDOW).apply(self.realized_volatility_daily)
            spy_data['vol_future'] = spy_data['vol_future'].bfill()
            volaT = np.percentile(spy_data['vol_current'], 50)
            volaH = np.percentile(spy_data['vol_current'], 80)
            allocation_dict = {self.tickers[i]: self.weights[i] for i in range(len(self.tickers))}

                # Check if the current ATR or Realized Volatility is above the 7th or 8th decile
            if (spy_data['vol_current'].iloc[-1] > spy_data['vol_future'].iloc[-1] and spy_data['vol_current'].iloc[-1] > volaT):

                allocation[self.RiskOn] = 0
                allocation[self.RiskOff] = 1.0
                if spy_data['vol_current'].iloc[-1] > volaH:
                    self.count = 20
                else:
                    self.count = 15
            elif self.count < 1:

                allocation[self.RiskOn] = 1.0
                allocation[self.RiskOff] = 0
            else:
                allocation[self.RiskOn] = 0
                allocation[self.RiskOff] = 1.0
            
            return TargetAllocation(allocation)
        else:
            allocation[self.RiskOn] = 0
            allocation[self.RiskOff] = 1.0
            return TargetAllocation(allocation)
