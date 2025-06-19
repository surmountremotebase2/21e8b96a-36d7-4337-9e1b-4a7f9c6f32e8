from surmount.base_class import Strategy, TargetAllocation
from surmount.data import DY, TenYearTreasuryConstMaturityRate, CboeVolatilityIndexVix

class TradingStrategy(Strategy):
    def __init__(self):
        # Define the assets: VYM (Vanguard High Dividend Yield ETF) and TLT (iShares 20+ Year Treasury Bond ETF)
        self.tickers = ["VYM", "TLT"]
        # Specify additional data sources for dividend yield, Treasury rate, and volatility index
        self.data_list = [DY("VYM"), TenYearTreasuryConstMaturityRate(), CboeVolatilityIndexVix()]

    @property
    def interval(self):
        # Use daily interval since dividend yields and Treasury rates are not intraday metrics
        return "1day"

    @property
    def assets(self):
        # Return the list of tickers to be traded
        return self.tickers

    @property
    def data(self):
        # Return the list of additional data sources
        return self.data_list

    def run(self, data):
        # Check if required data is available; return empty allocation if not
        if not data[("dy", "VYM")] or not data[("ten_year_treasury_const_maturity_rate",)] or not data[("cboe_volatility_index_vix",)]:
            return TargetAllocation({})

        # Extract the latest values from the data
        dy = data[("dy", "VYM")][-1]["value"]  # Latest dividend yield of VYM
        treasury_yield = data[("ten_year_treasury_const_maturity_rate",)][-1]["value"]  # Latest 10-year Treasury rate
        vix = data[("cboe_volatility_index_vix",)][-1]["value"]  # Latest VIX index value

        # Determine allocation based on market conditions
        if vix > 25:
            # High volatility scenario: prioritize capital preservation with more allocation to bonds
            allocation = {"VYM": 0.2, "TLT": 0.8}
        elif dy > treasury_yield + 0.01:
            # Attractive dividend yield scenario: favor stocks when yield exceeds Treasury rate by 1%
            allocation = {"VYM": 0.7, "TLT": 0.3}
        else:
            # Default scenario: balanced allocation when no strong signal is present
            allocation = {"VYM": 0.5, "TLT": 0.5}

        # Return the target allocation
        return TargetAllocation(allocation)