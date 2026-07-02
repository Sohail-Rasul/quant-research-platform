from app.strategies.base_strategy import Strategy
from app.universe.base_universe import BaseUniverse
from app.indicators.base_indicator import BaseIndicator
from app.ranking.base_ranker import BaseRanker
from app.weighting.base_weighting import BaseWeighting
from app.filters.base_filter import BaseFilter
from app.strategies.strategy_state import StrategyState

class PipelineStrategy(Strategy):
    def __init__(
        self,
        universe: BaseUniverse,
        indicators: list[BaseIndicator],
        ranker: BaseRanker,
        weighting: BaseWeighting,
        filters: list[BaseFilter] | None = None
    ):
        self.universe = universe
        self.indicators = indicators
        self.ranker = ranker
        self.weighting = weighting
        self.filters = filters or []

    
    def generate_weights(self, state : StrategyState):
        
        state.tickers = self.universe.get_tickers()

        state.selected_tickers = state.tickers.copy()

        #To clear indicator results and not reuse old data
        state.indicator_results.clear()

        #Calculating indicator result values
        for indicator in self.indicators :
            state.indicator_results[indicator.name] = indicator.calculate(state)

        for filter in self.filters:
            filter.apply(state)
        
        self.ranker.rank(state)

        return self.weighting.generate_weights(state)



        return {}
