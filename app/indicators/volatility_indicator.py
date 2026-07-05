from app.indicators.base_indicator import BaseIndicator
from app.strategies.strategy_state import StrategyState

import numpy as np
import pandas as pd

class VolatilityIndicator(BaseIndicator):
    def __init__(self,lookback_days : int):
        self.lookback_days = lookback_days

    @property
    def name(self):
        return "volatility"
    
    def calculate(self,state : StrategyState):
        #CALCULATE AND RETURN ANNUAL VOLATILITY

        #Validate History
        if len(state.historical_data) < (self.lookback_days+1):
            raise ValueError(f"Not enough data available. \n Required: {self.lookback_days + 1} rows of historical data \n Available: {len(state.historical_data)} ")

        #Get required historical data
        historical_data = state.historical_data.iloc[-(self.lookback_days+1):]
        historical_data = historical_data.astype(float)

        #daily returns
        daily_returns = historical_data.pct_change()

        #annualized volatility
        volatility = daily_returns.std(ddof=1) * np.sqrt(252) #ddof => delta degrees of freedom. ddof = 1 means we are using a sample of the stocks return distribution rather than the entire thing.

        return volatility



    @property
    def warmup_period(self):
        return self.lookback_days + 1
        # 2 prices -> 1 return | 3 prices -> 2 returns .... | 64 prices -> 63 returns
