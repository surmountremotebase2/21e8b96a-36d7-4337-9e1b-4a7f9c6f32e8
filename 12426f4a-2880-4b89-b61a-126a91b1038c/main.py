from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import RSI
from surmount.logging import log

class TradingStrategy(Strategy):
    def __init__(self):
        # Define the assets to trade: QQQ (long Nasdaq 100) and SQQQ (short Nasdaq 100)
        self.tickers = ["QQQ", "SQQQ"]
        # No additional data sources needed beyond OHLCV
        self.data_list = []

    @property
    def assets(self):
        # Return the list of tickers this strategy will trade
        return self.tickers

    @property
    def interval(self):
        # Set the data interval to hourly for intraday trading
        return "1hour"

    @property
    def data(self):
        # Return the data list (empty since we only use OHLCV)
        return self.data_list

    def run(self, data):
        # Extract OHLCV data from the input
        ohlcv = data["ohlcv"]
        
        # Calculate RSI for QQQ with a 14-period lookback
        rsi = RSI("QQQ", ohlcv, 14)
        
        # Check if RSI data is available and has at least one value
        if rsi is None or len(rsi) < 1:
            log("Not enough data to calculate RSI")
            return TargetAllocation({"QQQ": 0, "SQQQ": 0})
        
        # Get the latest RSI value
        latest_rsi = rsi[-1]
        
        # Get current holdings, defaulting to 0 if the asset isn't held
        holdings = data["holdings"]
        qqq_stake = holdings.get("QQQ", 0)
        sqqq_stake = holdings.get("SQQQ", 0)
        
        # Buy QQQ when RSI < 30 (oversold condition)
        if latest_rsi < 30:
            log("RSI < 30, buying QQQ")
            if qqq_stake >= 0:
                # Increase position by 0.1 if already holding, up to a max of 1
                qqq_stake = min(1, qqq_stake + 0.1)
            else:
                # Initial position if not holding
                qqq_stake = 0.2
            sqqq_stake = 0  # Exit any SQQQ position
        
        # Buy SQQQ when RSI > 70 (overbought condition)
        elif latest_rsi > 70:
            log("RSI > 70, buying SQQQ")
            if sqqq_stake >= 0:
                # Increase position by 0.1 if already holding, up to a max of 1
                sqqq_stake = min(1, sqqq_stake + 0.1)
            else:
                # Initial position if not holding
                sqqq_stake = 0.2
            qqq_stake = 0  # Exit any QQQ position
        
        # Manage existing positions when RSI is between 30 and 70
        else:
            # Sell QQQ if holding and RSI > 50 (exit condition)
            if qqq_stake > 0 and latest_rsi > 50:
                log("RSI > 50, selling QQQ")
                qqq_stake = 0
            # Sell SQQQ if holding and RSI < 50 (exit condition)
            if sqqq_stake > 0 and latest_rsi < 50:
                log("RSI < 50, selling SQQQ")
                sqqq_stake = 0
            # If no exit condition is met, stakes remain unchanged (hold position)
        
        # Return the target allocation with updated stakes
        return TargetAllocation({"QQQ": qqq_stake, "SQQQ": sqqq_stake})