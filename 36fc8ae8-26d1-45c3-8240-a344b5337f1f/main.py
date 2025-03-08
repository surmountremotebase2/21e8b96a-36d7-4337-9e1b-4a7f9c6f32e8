from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import RSI, BB
from surmount.logging import log

class TradingStrategy(Strategy):
    
    @property
    def assets(self):
        # Define which assets this strategy will trade.
        return ["QQQ"]

    @property
    def interval(self):
        # Set the interval for the trading strategy to '1hour'
        return "1hour"
    
    def run(self, data):
        # Initialize the allocation to none
        qqq_stake = 0
        
        # Compute RSI for QQQ
        rsi_values = RSI("QQQ", data["ohlcv"], 14)  # 14-period RSI
        
        # Compute Bollinger Bands and use their width as a volatility measure
        bollinger_bands = BB("QQQ", data["ohlcv"], 20, 2)  # 20-period Bollinger Bands with 2 std deviation
        if bollinger_bands and rsi_values:
            upper_band = bollinger_bands["upper"][-1]
            lower_band = bollinger_bands["lower"][-1]
            bb_width = upper_band - lower_band
            current_rsi = rsi_values[-1]
            
            # Low volatility filter
            low_volatility = bb_width < (upper_band + lower_band) * 0.05  # Arbitrary threshold for low volatility
            
            # Overbought/oversold conditions
            oversold = current_rsi < 30
            overbought = current_rsi > 70
            
            # Trade logic
            if low_volatility and oversold:
                log("Buying QQQ due to oversold RSI and low volatility")
                qqq_stake = 1  # Full allocation to QQQ
            elif low_volatility and overbought:
                log("Selling QQQ due to overbought RSI and low volatility")
                qqq_stake = 0  # No allocation to QQQ

        return TargetAllocation({"QQQ": qqq_stake})