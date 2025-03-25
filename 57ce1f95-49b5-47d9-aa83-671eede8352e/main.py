from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import RSI, SMA, ATR
from surmount.logging import log
from surmount.data import CPI

class TradingStrategy(Strategy):
    """
    A volatility-based & mean reversion trading strategy for Real Assets & Commodities.
    The strategy dynamically adjusts allocations based on inflation, price movements,
    and risk management rules.
    """
    
    @property
    def assets(self):
        return ["GLD", "BAM", "PLD", "XOM", "COP", "ET"]
    
    @property
    def interval(self):
        return "1day"
    
    @property
    def data(self):
        return [CPI()]
    
    def run(self, data):
        """
        Executes the trading strategy based on CPI, price trends, and risk management rules.
        """
        allocations = {asset: 1 / len(self.assets) for asset in self.assets}  # Equal weight initially
        ohlcv_data = data["ohlcv"]
        cpi_data = data.get("cpi", [])
        
        # Adjust for inflation (CPI)
        if cpi_data and cpi_data[-1]["value"] > 5:
            allocations["GLD"] += 0.05  # Hedge with gold
            allocations["XOM"] += 0.05  # Increase oil exposure
            log("CPI > 5%, increasing exposure to GLD and XOM")
        
        for ticker in self.assets:
            if ticker not in ohlcv_data[-1]:
                continue  # Skip if no recent data available
            
            close_prices = [day[ticker]["close"] for day in ohlcv_data]
            latest_price = close_prices[-1]
            
            # Profit-Taking Rule: If GLD rises >15% in a quarter, rebalance
            if ticker == "GLD" and (latest_price / close_prices[-63] - 1) > 0.15:
                allocations["GLD"] -= 0.05  # Trim profits
                log("GLD rose >15% in a quarter, reducing allocation")
            
            # Stop-Loss Rule: If oil stocks drop >10% in a month, trim allocation
            if ticker in ["XOM", "COP", "ET"] and (latest_price / close_prices[-21] - 1) < -0.10:
                allocations[ticker] -= 0.05  # Reduce exposure
                log(f"{ticker} dropped >10% in a month, trimming allocation")
        
        # Normalize allocations to sum to 1
        total_allocation = sum(allocations.values())
        normalized_allocations = {
            asset: alloc / total_allocation for asset, alloc in allocations.items()
        }
        
        return TargetAllocation(normalized_allocations)