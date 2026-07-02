from abc import ABC, abstractmethod
from app.strategies.strategy_state import StrategyState

#Which ones are the best?

class BaseRanker(ABC):

    @abstractmethod
    def rank(self, state : StrategyState): #Either composite results OR multiple series of each indicator output
        pass