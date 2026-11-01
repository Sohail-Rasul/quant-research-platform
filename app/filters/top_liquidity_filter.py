from app.filters.base_filter import BaseFilter
from app.strategies.strategy_state import StrategyState


class TopLiquidityFilter(BaseFilter):
    """
    Point-in-time universe built only from data that existed on the signal date:
    keep the `top_k` stocks with the highest average daily traded value
    (price * volume) over the last `lookback_days`.

    WHY: your universe is today's NSE 500 applied to every past date. This
    replaces "is in today's index" with "was among the most traded stocks
    on that date", which uses no hindsight. It does NOT add delisted stocks
    (they must exist in the prices table for that) - see the bias-check script.
    """

    def __init__(self, lookback_days: int, top_k: int):
        if top_k <= 0:
            raise ValueError("top_k must be greater than 0.")
        self.lookback_days = lookback_days
        self.top_k = top_k

    def apply(self, state: StrategyState):
        if state.volume_data is None:
            raise ValueError("TopLiquidityFilter requires state.volume_data.")

        prices = state.historical_data.iloc[-self.lookback_days:].astype(float)
        volumes = state.volume_data.iloc[-self.lookback_days:].astype(float)

        traded_value = (prices * volumes).mean()          # NaN if no data in window
        traded_value = traded_value.reindex(state.selected_tickers).dropna()

        keep = traded_value.sort_values(ascending=False).head(self.top_k).index
        state.selected_tickers = [t for t in state.selected_tickers if t in keep]
