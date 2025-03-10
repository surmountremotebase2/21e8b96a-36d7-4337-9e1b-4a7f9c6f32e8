from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import (
    RSI, SMA, EMA, MACD, MFI, BB, Slope, ADX, CCI, PPO, SO, WillR, 
    STDEV, VWAP, Momentum, PSAR, OBV, ATR
)
from surmount.logging import log

class TradingStrategy(Strategy):
    """
    A simple buy-and-hold strategy for QQQ that logs all available technical indicators.
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
        Execute the strategy: Allocate 100% to QQQ and log all technical indicators.
        
        :param data: Dictionary containing OHLCV data and other requested data
        :return: TargetAllocation object with portfolio allocation
        """
        # Access OHLCV data
        ohlcv_data = data["ohlcv"]
        
        # Check if there's enough data to calculate indicators
        if not ohlcv_data or len(ohlcv_data) < 20:
            log("Insufficient data to calculate indicators.")
            return TargetAllocation({"QQQ": 0})

        # Log all available technical indicators for QQQ
        ticker = "QQQ"

        # RSI (Relative Strength Index)
        rsi = RSI(ticker, ohlcv_data, length=14)
        log(f"RSI (14): {rsi[-1] if rsi else 'N/A'}")

        # SMA (Simple Moving Average)
        sma = SMA(ticker, ohlcv_data, length=20)
        log(f"SMA (20): {sma[-1] if sma else 'N/A'}")

        # EMA (Exponential Moving Average)
        ema = EMA(ticker, ohlcv_data, length=20)
        log(f"EMA (20): {ema[-1] if ema else 'N/A'}")

        # MACD (Moving Average Convergence Divergence)
        macd = MACD(ticker, ohlcv_data, fast=12, slow=26)
        if macd:
            log(f"MACD Line: {macd['MACD_12_26_9'][-1]}")
            log(f"MACD Signal: {macd['MACDs_12_26_9'][-1]}")
            log(f"MACD Histogram: {macd['MACDh_12_26_9'][-1]}")

        # MFI (Money Flow Index)
        mfi = MFI(ticker, ohlcv_data, length=14)
        log(f"MFI (14): {mfi[-1] if mfi else 'N/A'}")

        # BB (Bollinger Bands)
        bb = BB(ticker, ohlcv_data, length=20, std=2.0)
        if bb:
            log(f"BB Upper (20, 2): {bb['upper'][-1]}")
            log(f"BB Middle (20, 2): {bb['mid'][-1]}")
            log(f"BB Lower (20, 2): {bb['lower'][-1]}")

        # Slope
        slope = Slope(ticker, ohlcv_data, length=14)
        log(f"Slope (14): {slope[-1] if slope else 'N/A'}")

        # ADX (Average Directional Index)
        adx = ADX(ticker, ohlcv_data, length=14)
        log(f"ADX (14): {adx[-1] if adx else 'N/A'}")

        # CCI (Commodity Channel Index)
        cci = CCI(ticker, ohlcv_data, length=20)
        log(f"CCI (20): {cci[-1] if cci else 'N/A'}")

        # PPO (Percentage Price Oscillator)
        ppo = PPO(ticker, ohlcv_data, fast=12, slow=26)
        log(f"PPO (12, 26): {ppo[-1] if ppo else 'N/A'}")

        # SO (Stochastic Oscillator)
        so = SO(ticker, ohlcv_data)
        log(f"Stochastic Oscillator: {so[-1] if so else 'N/A'}")

        # Williams %R
        willr = WillR(ticker, ohlcv_data, length=14)
        log(f"Williams %R (14): {willr[-1] if willr else 'N/A'}")

        # STDEV (Standard Deviation)
        stdev = STDEV(ticker, ohlcv_data, length=20)
        log(f"STDEV (20): {stdev[-1] if stdev else 'N/A'}")

        # VWAP (Volume Weighted Average Price)
        vwap = VWAP(ticker, ohlcv_data, length=14)
        log(f"VWAP (14): {vwap[-1] if vwap else 'N/A'}")

        # Momentum
        momentum = Momentum(ticker, ohlcv_data, length=10)
        log(f"Momentum (10): {momentum[-1] if momentum else 'N/A'}")

        # PSAR (Parabolic SAR)
        psar = PSAR(ticker, ohlcv_data)
        log(f"PSAR: {psar[-1] if psar else 'N/A'}")

        # OBV (On-Balance Volume)
        obv = OBV(ticker, ohlcv_data, length=14)
        log(f"OBV (14): {obv[-1] if obv else 'N/A'}")

        # ATR (Average True Range)
        atr = ATR(ticker, ohlcv_data, length=14)
        log(f"ATR (14): {atr[-1] if atr else 'N/A'}")

        # Simple buy-and-hold allocation: 100% to QQQ
        allocation_dict = {"QQQ": 1.0}
        return TargetAllocation(allocation_dict)