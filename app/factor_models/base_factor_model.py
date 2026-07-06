from abc import ABC, abstractmethod
from app.strategies.strategy_state import StrategyState

class BaseFactorModel(ABC):

    @abstractmethod
    def calculate(self, state : StrategyState):
        pass