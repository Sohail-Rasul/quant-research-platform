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

        # Only rank stocks that have survived all previous pipeline stages
        # (Universe -> Indicators -> Filters -> Ranker).
        # Only rank stocks that survived previous pipeline stages.

        indicator_values = state.indicator_results[self.indicator]

        valid_tickers = [
            ticker
            for ticker in state.selected_tickers
            if ticker in indicator_values.index
            and pd.notna(indicator_values.loc[ticker])
        ]

        indicator_values = indicator_values.loc[valid_tickers]

        state.selected_tickers = valid_tickers

        #Sort in requested direction and get top n stocks
        top_stocks = indicator_values.sort_values(ascending=self.ascending).head(self.n) # This gives stock : value but we only need stock now for selected tickers as a list
        print(f"TOP {self.n}:")
        print(top_stocks)


        state.selected_tickers = top_stocks.index.tolist() #We are consistently using list everywhere so we convert pandas index to list

        # FIX: this used to print the configured `self.n` instead of the actual
        # number of stocks selected, which can be lower than n if fewer stocks
        # pass the eligibility/NaN checks. Cosmetic only — does not affect returns.
        print(
            f"{state.date} | "
            f"Eligible stocks: {len(valid_tickers)} | "
            f"Selected: {len(state.selected_tickers)}"
        )