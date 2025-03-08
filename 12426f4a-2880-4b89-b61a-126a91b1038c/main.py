from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import RSI, ATR
from surmount.logging import log

class TradingStrategy(Strategy):
    """
    A strategy that trades QQQ hourly based on RSI and volatility (ATR) filtering.
    - Buys when RSI indicates oversold conditions and volatility is within a moderate range.
    - Sells (or avoids allocation) when RSI indicates overbought conditions.
    - Uses ATR to filter out excessive volatility to reduce risk.
    """

    @property
    def assets(self):
        # Define the asset to trade: QQQ
        return ["QQQ"]

    @property
    def interval(self):
        # Set the data interval to hourly for intraday trading
        return "1hour"

    @property
    def data(self):
        # No additional data sources needed beyond OHLCV
        return []

    def run(self, data):
        """
        Execute the trading strategy based on RSI and volatility (ATR).
        
        :param data: Dictionary containing OHLCV data and other requested data sources
        :return: TargetAllocation object with allocation for QQQ
        """
        # Access OHLCV data
        ohlcv_data = data["ohlcv"]
        
        # Check if there’s enough data to calculate indicators (RSI needs 14 periods, ATR needs 14)
        if len(ohlcv_data) < 14:
            log("Insufficient data to calculate RSI and ATR")
            return TargetAllocation({"QQQ": 0})

        # Calculate RSI with a 14-period lookback (standard setting)
        rsi_values = RSI("QQQ", ohlcv_data, length=14)
        if rsi_values is None or len(rsi_values) == 0:
            log("RSI calculation failed")
            return TargetAllocation({"QQQ": 0})

        # Calculate ATR with a 14-period lookback to measure volatility
        atr_values = ATR("QQQ", ohlcv_data, length=14)
        if atr_values is None or len(atr_values) == 0:
            log("ATR calculation failed")
            return TargetAllocation({"QQQ": 0})

        # Get the latest values
        current_rsi = rsi_values[-1]
        current_atr = atr_values[-1]
        current_price = ohlcv_data[-1]["QQQ"]["close"]

        # Define RSI thresholds
        oversold_threshold = 30  # RSI below 30 indicates oversold
        overbought_threshold = 70  # RSI above 70 indicates overbought

        # Define volatility filter: Use ATR as a percentage of price
        atr_percentage = (current_atr / current_price) * 100
        moderate_volatility_range = (0.5, 2.0)  # ATR between 0.5% and 2% of price

        # Initialize allocation
        qqq_allocation = 0

        # Trading logic
        if current_rsi < oversold_threshold:
            # Potential buy signal: Check volatility
            if moderate_volatility_range[0] <= atr_percentage <= moderate_volatility_range[1]:
                log(f"Oversold RSI ({current_rsi:.2f}) with moderate volatility (ATR% = {atr_percentage:.2f}) - Buying QQQ")
                qqq_allocation = 1  # Full allocation to QQQ
            else:
                log(f"Oversold RSI ({current_rsi:.2f}) but volatility out of range (ATR% = {atr_percentage:.2f}) - No trade")
        elif current_rsi > overbought_threshold:
            # Overbought: Avoid allocation
            log(f"Overbought RSI ({current_rsi:.2f}) - No allocation to QQQ")
            qqq_allocation = 0
        else:
            # Neutral RSI: Maintain no position unless already holding
            log(f"Neutral RSI ({current_rsi:.2f}) - No change in allocation")
            qqq_allocation = 0

        # Return the allocation dictionary wrapped in TargetAllocation
        return TargetAllocation({"QQQ": qqq_allocation})