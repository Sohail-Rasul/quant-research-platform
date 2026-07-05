from app.ranking.base_ranker import BaseRanker
from app.strategies.strategy_state import StrategyState
import pandas as pd


class TopNRanker(BaseRanker):
    def __init__(self,indicator: str , n:int, ascending : bool = False):
        self.indicator = indicator
        self.n = n
        self.ascending = ascending

        if n <= 0:
            raise ValueError("n must be greater than 0.")

    def rank(self, state : StrategyState):
        indicator_values = state.indicator_results[self.indicator]

        # Only rank stocks that have survived all previous pipeline stages
        # (Universe -> Indicators -> Filters -> Ranker).

        indicator_values = indicator_values.loc[state.selected_tickers] # Only rank stocks that survived previous pipeline stages.

        #Sort in requested direction and get top n stocks
        top_stocks = indicator_values.sort_values(ascending=self.ascending).head(self.n) # This gives stock : value but we only need stock now for selected tickers as a list

        state.selected_tickers = top_stocks.index.tolist() #We are consistently using list everywhere so we convert pandas index to list

