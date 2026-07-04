from app.ranking.base_ranker import BaseRanker
from app.strategies.strategy_state import StrategyState
import pandas as pd


class TopNRanker(BaseRanker):
    def __init__(self,indicator: str , n:int):
        self.indicator = indicator
        self.n = n

    def rank(self, state : StrategyState):
        indicator_values = state.indicator_results[self.indicator]

        # Only rank stocks that have survived all previous pipeline stages
        # (Universe -> Indicators -> Filters -> Ranker).

        indicator_values = indicator_values.loc[state.selected_tickers] # We add this because without this it would rank all the stocks in universe even after previous filters or ranking if any

        #Sort in descending and get top n stocks
        top_stocks = indicator_values.sort_values(ascending=False).head(self.n) # This gives stock : value but we only need stock now for selected tickers as a list

        state.selected_tickers = top_stocks.index.tolist() #We are consistently using list everywhere so we convert pandas index to list

