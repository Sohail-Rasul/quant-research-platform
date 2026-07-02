from app.filters.base_filter import BaseFilter
from app.strategies.strategy_state import StrategyState

class NoFilter(BaseFilter):

    def apply(self,state : StrategyState):

        pass