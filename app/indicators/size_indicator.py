from app.indicators.base_indicator import BaseIndicator
from app.strategies.strategy_state import StrategyState

import numpy as np

class SizeIndicator(BaseIndicator):

    @property
    def name(self):
        return "size"
    
    def calculate(self, state : StrategyState):
        if state.metadata is None:
            raise ValueError("SizeIndicator requires metadata.")

        # KNOWN ISSUE (not fixed here — needs a schema change, not a code patch):
        # `state.metadata["shares_outstanding"]` is a single static, current-day
        # value (see stocks.shares_outstanding in the DB — it has no date column
        # and is overwritten in place every time metadata is refreshed).
        # That means every historical market-cap calculation below uses TODAY's
        # share count, even though real shares outstanding changes over time via
        # splits, bonus issues, buybacks, and rights issues. This is a real
        # look-ahead / staleness bug in the size factor.
        # Proper fix: add a `shares_outstanding_history(stock_id, effective_date,
        # shares_outstanding)` table and do an as-of join on signal_date here,
        # instead of reading the static `stocks.shares_outstanding` column.
        # Until that data exists, treat "size" as a current-shares proxy, not a
        # true historical size factor — consider reducing its weight or excluding
        # it from the composite score.
        latest_prices = state.historical_data.iloc[-1].astype(float)
        shares = state.metadata.loc[latest_prices.index , "shares_outstanding"]

        if shares.isnull().any():
            raise ValueError("Missing shares outstanding for one or more tickers.")

        market_cap = shares * latest_prices
        size = np.log(market_cap)

        return size
        
    
    @property
    def warmup_period(self):
        return 1 #History Not Needed