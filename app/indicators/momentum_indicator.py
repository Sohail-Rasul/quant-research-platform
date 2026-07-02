from app.indicators.base_indicator import BaseIndicator
from app.strategies.strategy_state import StrategyState
import pandas as pd

class MomentumIndicator(BaseIndicator):
    def __init__(self,lookback_days:int):
        self.lookback_days = lookback_days

    @property
    def name(self):
        return "momentum"

    def calculate(self,state : StrategyState) -> pd.Series:

        if len(state.historical_data) < (self.lookback_days+1):
            raise ValueError(f"Not enough data available. \n Required: {self.lookback_days + 1} rows of historical data \n Available: {len(state.historical_data)} ")

        today_price = state.historical_data.iloc[-1]
        past_price = state.historical_data.iloc[-(self.lookback_days+1)]

        momentum = (today_price / past_price) -1

        return momentum
