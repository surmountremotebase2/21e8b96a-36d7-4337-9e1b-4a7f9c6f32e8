from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import BB, MACD
from surmount.logging import log
from surmount.data import SocialSentiment

class TradingStrategy(Strategy):
    def __init__(self):
        self.ticker = "AAPL"
        self.data_list = [SocialSentiment(self.ticker)]
    
    @property
    def interval(self):
        return "1day"
    
    @property
    def assets(self):
        return [self.ticker]
    
    @property
    def data(self):
        return self.data_list
    
    def run(self, data):
        sentiment_data = data[("social_sentiment", self.ticker)]
        if not sentiment_data:
            log("No social sentiment data available.")
            return TargetAllocation({self.ticker: 0})
        
        latest_sentiment = sentiment_data[-1]["twitterSentiment"]
        bb = BB(self.ticker, data["ohlcv"], 20)
        macd = MACD(self.ticker, data["ohlcv"], fast=12, slow=26)
        
        if not bb or not macd:
            log("BB or MACD calculation failed.")
            return TargetAllocation({self.ticker: 0})
        
        current_price = data["ohlcv"][-1][self.ticker]["close"]
        lower_bb = bb["lower"][-1]
        upper_bb = bb["upper"][-1]
        macd_histogram = macd["histogram"][-1]
        
        sentiment_factor = latest_sentiment - 0.5  # Scale sentiment contribution
        price_factor = (upper_bb - current_price) / (upper_bb - lower_bb)  # Inverse relation to closeness to upper BB
        momentum_factor = macd_histogram  # Direct relation to bullish momentum
        
        allocation_score = (sentiment_factor + price_factor + momentum_factor) / 3  # Normalizing the influence
        
        # Ensuring allocation is within bounds
        allocation = min(1, max(0, allocation_score))
        
        log(f"Allocation for {self.ticker}: {allocation}")
        return TargetAllocation({self.ticker: allocation})