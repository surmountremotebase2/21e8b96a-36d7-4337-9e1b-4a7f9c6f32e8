from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import SMA, ATR
from surmount.data import CPI
from surmount.logging import log

class TradingStrategy(Strategy):
    """
    A strategy for real assets and commodities based on volatility and mean reversion.
    Adjusts allocation based on CPI data, price movements, and technical indicators.
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
        allocations = {ticker: 1 / len(self.assets) for ticker in self.assets}  # Equal weight initially
        ohlcv = data["ohlcv"]
        cpi_data = data.get("cpi")
        
        if cpi_data and cpi_data[-1]["value"] > 5:
            allocations["GLD"] += 0.05  # Increase gold exposure
            allocations["XOM"] += 0.05  # Increase oil exposure
            log("High inflation detected, increasing GLD and XOM allocations.")
        
        for ticker in self.assets:
            close_prices = [day["close"] for day in ohlcv if ticker in day]
            if len(close_prices) < 2:
                continue  # Skip if not enough data
            
            recent_return = (close_prices[-1] - close_prices[-2]) / close_prices[-2]  # Daily return
            atr_value = ATR(ticker, ohlcv, length=14)[-1]
            sma_value = SMA(ticker, ohlcv, length=20)[-1]
            
            if ticker == "GLD" and recent_return > 0.15:
                allocations["GLD"] -= 0.05  # Reduce exposure after strong rally
                log("GLD profit-taking triggered.")
            
            if ticker in ["XOM", "COP"] and recent_return < -0.10:
                allocations[ticker] -= 0.05  # Reduce oil exposure on significant drop
                log(f"Stop-loss triggered for {ticker}.")
            
            if sma_value and close_prices[-1] < sma_value:
                allocations[ticker] += 0.02  # Mean reversion: Buy undervalued assets
                log(f"{ticker} below SMA, increasing allocation.")
        
        total_alloc = sum(allocations.values())
        normalized_allocations = {k: v / total_alloc for k, v in allocations.items()}
        return TargetAllocation(normalized_allocations)