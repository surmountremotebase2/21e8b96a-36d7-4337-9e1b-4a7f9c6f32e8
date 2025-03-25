from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import SMA
from surmount.data import HousingCPI
from surmount.logging import log

class TradingStrategy(Strategy):
    """
    A volatility-based and mean reversion strategy focused on real assets and commodities.
    The strategy dynamically allocates to GLD, BAM, PLD, XOM, COP, and ET based on inflation data,
    gold price movements, and oil stock performance.
    """

    @property
    def assets(self):
        return ["GLD", "BAM", "PLD", "XOM", "COP", "ET"]

    @property
    def interval(self):
        return "1day"

    @property
    def data(self):
        return [HousingCPI()]

    def run(self, data):
        """
        Executes the trading strategy logic.
        
        Args:
            data (dict): Contains OHLCV price data and CPI inflation data.
        
        Returns:
            TargetAllocation: The target allocations for each asset.
        """
        allocations = {ticker: 1 / len(self.assets) for ticker in self.assets}  # Default equal allocation
        ohlcv = data["ohlcv"]
        cpi_data = data.get("HousingCPI")

        if len(ohlcv) < 50:
                continue  # Ensure sufficient data

        current_cpi = cpi_data[-1]["value"]
        # Rebalance based on CPI Inflation Data
        if cpi_data[-1]["value"] > 5.0:
            allocations["GLD"] += 0.10  # Increase gold allocation
            allocations["XOM"] += 0.10  # Increase oil allocation
            log("High inflation detected (CPI > 5%), increasing allocation to GLD and XOM")

        # Profit-Taking Rule: If GLD rises >15% in a quarter, rebalance
        gld_prices = [ohlcv[i]["GLD"]["close"] for i in range(-63, 0)]  # Approx. 63 trading days in a quarter
        if gld_prices[0] and gld_prices[-1] and ((gld_prices[-1] - gld_prices[0]) / gld_prices[0]) > 0.15:
            allocations["GLD"] -= 0.10  # Reduce allocation to GLD
            log("GLD up more than 15% this quarter, reducing allocation")
            log(f"CPI - {current_cpi}")

        # Stop-Loss Rule: If oil stocks drop >10% in a month, trim allocation
        for ticker in ["XOM", "COP"]:
            stock_prices = [ohlcv[i][ticker]["close"] for i in range(-21, 0)]  # Approx. 21 trading days in a month
            if stock_prices[0] and stock_prices[-1] and ((stock_prices[-1] - stock_prices[0]) / stock_prices[0]) < -0.10:
                allocations[ticker] -= 0.05  # Reduce exposure to oil stocks
                log(f"{ticker} dropped more than 10% this month, trimming allocation")
                log(f"CPI - {current_cpi}")

        # Normalize allocations to ensure they sum to 1
        total_allocation = sum(allocations.values())
        normalized_allocations = {asset: alloc / total_allocation for asset, alloc in allocations.items()}

        return TargetAllocation(normalized_allocations)