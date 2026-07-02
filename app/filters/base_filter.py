from abc import ABC, abstractmethod
from app.strategies.strategy_state import StrategyState

#Should this stock continue?
# Modifies state.selected_tickers based on the strategy rules.
class BaseFilter(ABC):

    @abstractmethod
    def apply(self,state : StrategyState): #Either composite results OR multiple series of each indicator output
        pass