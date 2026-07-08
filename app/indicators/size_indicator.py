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