from app.strategies.base_strategy import Strategy
from app.universe.base_universe import BaseUniverse
from app.indicators.base_indicator import BaseIndicator
from app.ranking.base_ranker import BaseRanker
from app.weighting.base_weighting import BaseWeighting
from app.filters.base_filter import BaseFilter
from app.strategies.strategy_state import StrategyState
from app.factor_models.base_factor_model import BaseFactorModel

class PipelineStrategy(Strategy):
    def __init__(
        self,
        universe: BaseUniverse,
        indicators: list[BaseIndicator],
        ranker: BaseRanker,
        weighting: BaseWeighting,
        filters: list[BaseFilter] | None = None,
        factor_model: BaseFactorModel | None = None,
        universe_filters: list[BaseFilter] | None = None
    ):
        self.universe = universe
        self.indicators = indicators
        self.ranker = ranker
        self.weighting = weighting
        self.filters = filters or []
        self.factor_model = factor_model

        # NEW: filters that DEFINE the investable universe (e.g. liquidity).
        # They run BEFORE indicators so the factor model's z-scores are
        # computed only across stocks you could actually buy. Regular
        # `filters` still run after the factor model, exactly as before.
        self.universe_filters = universe_filters or []

    
    def generate_weights(self, state : StrategyState):

        # NEW: optional hook for a point-in-time universe (one that knows
        # which tickers were ACTUALLY index constituents on state.date,
        # instead of always returning today's constituent list). This is
        # part of addressing the survivorship-bias finding in the audit —
        # see app/universe/point_in_time_universe.py. UserUniverse (the
        # current default) has no set_date method, so this is skipped and
        # behavior is completely unchanged unless you opt into the new class.
        if hasattr(self.universe, "set_date"):
            self.universe.set_date(state.date)

        state.tickers = self.universe.get_tickers()

        state.selected_tickers = state.tickers.copy()

        # NEW: shrink the universe to investable stocks before any scoring.
        for universe_filter in self.universe_filters:
            universe_filter.apply(state)

        #To clear indicator results and not reuse old data
        state.indicator_results.clear()

        #Calculating indicator result values
        for indicator in self.indicators :
            state.indicator_results[indicator.name] = indicator.calculate(state)

        #Calculating Composite Factor
        if self.factor_model is not None:
            self.factor_model.calculate(state)


        for filter in self.filters:
            filter.apply(state)
        
        self.ranker.rank(state)

        return self.weighting.generate_weights(state)

