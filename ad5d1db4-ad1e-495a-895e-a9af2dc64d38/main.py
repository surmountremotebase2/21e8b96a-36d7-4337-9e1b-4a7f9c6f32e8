from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import SMA, RSI
from surmount.logging import log

class TradingStrategy(Strategy):
    def __init__(self):
        self.tickers = ["GLD", "BAM", "PLD", "XOM", "COP", "ET"]
        self.data_list = []
    
    @property
    def assets(self):
        return self.tickers
    
    @property
    def interval(self):
        return "1day"
    
    @property
    def data(self):
        return self.data_list
    
    def run(self, data):
        """
        Trading strategy that dynamically adjusts allocations based on CPI, mean reversion, and volatility.
        """
        cpi = data.get("cpi", {}).get("value", 2.0)  # Assume a default CPI value if missing
        ohlcv = data.get("ohlcv", [])
        allocation = {ticker: 1 / len(self.tickers) for ticker in self.tickers}  # Default equal allocation
        
        if not ohlcv:
            return TargetAllocation(allocation)
        
        # Adjust allocation if CPI is high (inflation hedge)
        if cpi > 5.0:
            allocation["GLD"] += 0.1
            allocation["XOM"] += 0.1
            log("Increased GLD and XOM exposure due to high CPI")
        
        # Profit-taking rule for GLD
        gld_prices = [entry["GLD"]["close"] for entry in ohlcv if "GLD" in entry]
        if len(gld_prices) > 1 and (gld_prices[-1] / gld_prices[0] - 1) > 0.15:
            allocation["GLD"] -= 0.1  # Reduce exposure after strong run-up
            log("Reduced GLD exposure due to 15% gain in a quarter")
        
        # Stop-loss rule for oil stocks (XOM, COP, ET)
        for ticker in ["XOM", "COP", "ET"]:
            prices = [entry[ticker]["close"] for entry in ohlcv if ticker in entry]
            if len(prices) > 20 and (prices[-1] / prices[-21] - 1) < -0.1:  # 10% monthly drop
                allocation[ticker] -= 0.1
                log(f"Trimmed {ticker} allocation due to 10% monthly drop")
        
        # Normalize allocations to keep sum between 0 and 1
        total_allocation = sum(allocation.values())
        if total_allocation > 1:
            scale_factor = 1 / total_allocation
            allocation = {k: v * scale_factor for k, v in allocation.items()}
        
        return TargetAllocation(allocation)