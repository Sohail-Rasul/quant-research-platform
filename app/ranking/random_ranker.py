import numpy as np
import pandas as pd

from app.ranking.base_ranker import BaseRanker
from app.strategies.strategy_state import StrategyState


class RandomRanker(BaseRanker):
    """
    Baseline: picks n RANDOM stocks from the same eligible set the real ranker
    would use (stocks with a valid value for `indicator`). If random picks earn
    a similar CAGR to your factor model, the universe/period is doing the work,
    not the factors.
    """

    def __init__(self, indicator: str, n: int, seed: int = 0):
        self.indicator = indicator
        self.n = n
        self.rng = np.random.default_rng(seed)

    def rank(self, state: StrategyState):
        values = state.indicator_results[self.indicator]
        eligible = [
            t for t in state.selected_tickers
            if t in values.index and pd.notna(values.loc[t])
        ]
        k = min(self.n, len(eligible))
        picked = list(self.rng.choice(eligible, size=k, replace=False)) if k else []
        state.selected_tickers = picked
