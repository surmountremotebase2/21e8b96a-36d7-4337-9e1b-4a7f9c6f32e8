from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import (RSI, SMA, EMA, MACD, MFI, BB, 
                                          Slope, ADX, CCI, PPO, SO, WillR, 
                                          STDEV, VWAP, Momentum, PSAR, OBV, ATR)
from surmount.logging import log

class TradingStrategy(Strategy):
    """
    A simple buy-and-hold strategy for QQQ that logs all available technical indicators.
    The strategy allocates 100% to QQQ and maintains the position while providing
    comprehensive indicator logging for analysis.
    """

    @property
    def assets(self):
        """Define the assets to trade."""
        return ["QQQ"]

    @property
    def interval(self):
        """Set the data interval to daily."""
        return "1day"

    @property
    def data(self):
        """No additional data sources needed for this strategy."""
        return []

    def run(self, data):
        """
        Execute the trading strategy.
        Args:
            data: Dictionary containing OHLCV data and other requested data sources
        Returns:
            TargetAllocation: Allocation dictionary with values summing between 0 and 1
        """
        # Check if we have enough data
        if not data["ohlcv"] or len(data["ohlcv"]) < 2:
            log("Insufficient data to calculate indicators")
            return TargetAllocation({"QQQ": 0})

        # Extract QQQ data
        ticker = "QQQ"
        ohlcv_data = data["ohlcv"]

        # Log all available technical indicators
        try:
            # Basic indicators with standard parameters
            log(f"RSI (14): {RSI(ticker, ohlcv_data, 14)[-1] if RSI(ticker, ohlcv_data, 14) else 'N/A'}")
            log(f"SMA (20): {SMA(ticker, ohlcv_data, 20)[-1] if SMA(ticker, ohlcv_data, 20) else 'N/A'}")
            log(f"EMA (20): {EMA(ticker, ohlcv_data, 20)[-1] if EMA(ticker, ohlcv_data, 20) else 'N/A'}")
            
            # MACD
            macd = MACD(ticker, ohlcv_data, 12, 26)
            if macd:
                log(f"MACD Line: {macd['MACD'][-1]}")
                log(f"MACD Signal: {macd['signal'][-1]}")
                log(f"MACD Histogram: {macd['histogram'][-1]}")
            
            log(f"MFI (14): {MFI(ticker, ohlcv_data, 14)[-1] if MFI(ticker, ohlcv_data, 14) else 'N/A'}")
            
            # Bollinger Bands
            bb = BB(ticker, ohlcv_data, 20, 2)
            if bb:
                log(f"BB Upper: {bb['upper'][-1]}")
                log(f"BB Middle: {bb['mid'][-1]}")
                log(f"BB Lower: {bb['lower'][-1]}")
            
            log(f"Slope (5): {Slope(ticker, ohlcv_data, 5)[-1] if Slope(ticker, ohlcv_data, 5) else 'N/A'}")
            log(f"ADX (14): {ADX(ticker, ohlcv_data, 14)[-1] if ADX(ticker, ohlcv_data, 14) else 'N/A'}")
            log(f"CCI (20): {CCI(ticker, ohlcv_data, 20)[-1] if CCI(ticker, ohlcv_data, 20) else 'N/A'}")
            log(f"PPO (12,26): {PPO(ticker, ohlcv_data, 12, 26)[-1] if PPO(ticker, ohlcv_data, 12, 26) else 'N/A'}")
            log(f"SO: {SO(ticker, ohlcv_data)[-1] if SO(ticker, ohlcv_data) else 'N/A'}")
            log(f"Williams %R (14): {WillR(ticker, ohlcv_data, 14)[-1] if WillR(ticker, ohlcv_data, 14) else 'N/A'}")
            log(f"STDEV (20): {STDEV(ticker, ohlcv_data, 20)[-1] if STDEV(ticker, ohlcv_data, 20) else 'N/A'}")
            log(f"VWAP (14): {VWAP(ticker, ohlcv_data, 14)[-1] if VWAP(ticker, ohlcv_data, 14) else 'N/A'}")
            log(f"Momentum (10): {Momentum(ticker, ohlcv_data, 10)[-1] if Momentum(ticker, ohlcv_data, 10) else 'N/A'}")
            log(f"PSAR: {PSAR(ticker, ohlcv_data)[-1] if PSAR(ticker, ohlcv_data) else 'N/A'}")
            log(f"OBV: {OBV(ticker, ohlcv_data)[-1] if OBV(ticker, ohlcv_data) else 'N/A'}")
            log(f"ATR (14): {ATR(ticker, ohlcv_data, 14)[-1] if ATR(ticker, ohlcv_data, 14) else 'N/A'}")

            # Log current price for reference
            current_price = ohlcv_data[-1][ticker]["close"]
            log(f"Current Price: {current_price}")

        except Exception as e:
            log(f"Error calculating indicators: {str(e)}")

        # Simple buy-and-hold strategy: always allocate 100% to QQQ
        allocation_dict = {"QQQ": 1.0}
        
        return TargetAllocation(allocation_dict)