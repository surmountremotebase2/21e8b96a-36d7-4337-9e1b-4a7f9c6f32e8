from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import MACD, EMA
from surmount.logging import log
import pandas as pd
import numpy as np

class TradingStrategy(Strategy):
    """
    A daily trading strategy for GLD using MACD and Hull Moving Average (HMA).
    - Entry: MACD line > 0, histogram turns positive, 15-period HMA sloping upwards.
    - Exit: After 3 bullish days in a row, 10 trading days, or 5% stop loss.
    """

    def __init__(self):
        # Initialize state variables to track position
        self.days_held = 0  # Number of days the position has been held
        self.entry_price = None  # Price at which GLD was bought
        self.bullish_days = 0  # Count of consecutive bullish days

    @property
    def assets(self):
        # Define the asset to trade: GLD
        return ["GLD"]

    @property
    def interval(self):
        # Set the data interval to daily
        return "1day"

    @property
    def data(self):
        # No additional data sources needed beyond OHLCV
        return []

    def _calculate_hma(self, data, ticker, period=15):
        """
        Calculate the 15-period Hull Moving Average (HMA).
        HMA = WMA(2 * WMA(n/2) - WMA(n), sqrt(n))
        """
        close_prices = [bar[ticker]["close"] for bar in data]
        if len(close_prices) < period:
            return None
        
        series = pd.Series(close_prices)
        
        # Step 1: Calculate WMA of period n
        wma_n = series.rolling(window=period).apply(
            lambda x: np.dot(x, np.arange(1, period + 1)) / sum(range(1, period + 1)), raw=True
        )
        
        # Step 2: Calculate WMA of period n/2
        half_period = period // 2
        wma_half = series.rolling(window=half_period).apply(
            lambda x: np.dot(x, np.arange(1, half_period + 1)) / sum(range(1, half_period + 1)), raw=True
        )
        
        # Step 3: Calculate 2 * WMA(n/2) - WMA(n)
        raw_hma = 2 * wma_half - wma_n
        
        # Step 4: Calculate WMA of the result with period sqrt(n)
        sqrt_period = int(np.sqrt(period))
        hma = raw_hma.rolling(window=sqrt_period).apply(
            lambda x: np.dot(x, np.arange(1, sqrt_period + 1)) / sum(range(1, sqrt_period + 1)), raw=True
        )
        
        return hma.tolist()

    def run(self, data):
        """
        Execute the trading strategy for GLD.
        
        :param data: Dictionary containing OHLCV data and holdings
        :return: TargetAllocation object with allocation for GLD
        """
        ohlcv_data = data["ohlcv"]
        holdings = data["holdings"]
        current_price = ohlcv_data[-1]["GLD"]["close"]

        # Check if there's enough data (MACD 12,26 needs at least 26 periods + buffer)
        if len(ohlcv_data) < 34:  # 26 for MACD slow + 8 for signal + buffer
            log("Insufficient data for MACD and HMA")
            return TargetAllocation({"GLD": 0})

        # Calculate MACD (12, 26, 9 default settings)
        macd_data = MACD("GLD", ohlcv_data, fast=12, slow=26)
        if macd_data is None or len(macd_data["MACD"]) < 2:
            log("MACD calculation failed")
            return TargetAllocation({"GLD": 0})

        # Get latest and previous MACD values
        macd_line = macd_data["MACD"][-1]
        histogram = macd_data["histogram"][-1]
        prev_histogram = macd_data["histogram"][-2]

        # Calculate 15-period HMA
        hma_values = self._calculate_hma(ohlcv_data, "GLD", period=15)
        if hma_values is None or len(hma_values) < 2:
            log("HMA calculation failed")
            return TargetAllocation({"GLD": 0})
        
        hma_current = hma_values[-1]
        hma_prev = hma_values[-2]

        # Determine if currently holding GLD
        gld_holding = holdings.get("GLD", 0) > 0

        # Initialize allocation
        gld_allocation = 0

        if gld_holding:
            # Track holding period and bullish days
            self.days_held += 1
            is_bullish = current_price > ohlcv_data[-2]["GLD"]["close"]
            self.bullish_days = self.bullish_days + 1 if is_bullish else 0

            # Check stop loss (5% below entry price)
            stop_loss_price = self.entry_price * 0.95
            if current_price <= stop_loss_price:
                log(f"Stop loss triggered at {current_price:.2f} (entry: {self.entry_price:.2f})")
                self._reset_position()
                return TargetAllocation({"GLD": 0})

            # Exit conditions
            if self.bullish_days >= 3:
                log(f"Exiting after 3 bullish days in a row")
                self._reset_position()
                return TargetAllocation({"GLD": 0})
            elif self.days_held >= 10:
                log(f"Exiting after 10 trading days")
                self._reset_position()
                return TargetAllocation({"GLD": 0})

            # Continue holding
            gld_allocation = 1
        else:
            # Entry conditions
            macd_above_zero = macd_line > 0
            histogram_up = histogram > 0
            histogram_cross = prev_histogram < 0
            hma_sloping_up = hma_current > hma_prev

            if (macd_above_zero and histogram_up and histogram_cross and hma_sloping_up):
                log(f"Entry signal: MACD {macd_line:.2f}, Hist {histogram:.2f} (prev {prev_histogram:.2f}), HMA sloping up")
                self.entry_price = current_price
                self.days_held = 0
                self.bullish_days = 0
                gld_allocation = 1
            else:
                log("No entry signal met")

        return TargetAllocation({"GLD": gld_allocation})

    def _reset_position(self):
        """Reset position tracking variables."""
        self.days_held = 0
        self.entry_price = None
        self.bullish_days = 0