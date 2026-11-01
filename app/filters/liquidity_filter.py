from app.filters.base_filter import BaseFilter
from app.strategies.strategy_state import StrategyState


class LiquidityFilter(BaseFilter):
    """
    NEW FILTER (added to address audit finding: no liquidity filter existed,
    so the ranker was free to select thinly-traded small/micro-cap stocks
    whose real bid-ask spread and market impact are far higher than the
    flat `transaction_cost` assumption models).

    Excludes any stock whose average daily traded value (price * volume)
    over `lookback_days` is below `min_avg_traded_value`.

    This does NOT fix survivorship bias — it only removes stocks that would
    be impractical to actually trade at meaningful size, which is a
    separate (and easier) problem to fix with existing data.
    """

    def __init__(self, lookback_days: int, min_avg_traded_value: float):
        self.lookback_days = lookback_days
        self.min_avg_traded_value = min_avg_traded_value

    def apply(self, state: StrategyState):
        if state.volume_data is None:
            raise ValueError(
                "LiquidityFilter requires state.volume_data. "
                "Make sure BacktestEngine is passing volume_data into StrategyState."
            )

        prices = state.historical_data.iloc[-self.lookback_days:].astype(float)
        volumes = state.volume_data.iloc[-self.lookback_days:].astype(float)

        # Average daily traded value per stock over the lookback window.
        # NaN-safe: a stock with no data at all in the window will produce
        # NaN here, and NaN < threshold is False, so it's correctly excluded
        # below rather than accidentally passing the filter.
        avg_traded_value = (prices * volumes).mean()

        eligible = avg_traded_value[avg_traded_value >= self.min_avg_traded_value].index

        # Only keep tickers that are both already selected AND liquid enough.
        state.selected_tickers = [
            ticker for ticker in state.selected_tickers if ticker in eligible
        ]
