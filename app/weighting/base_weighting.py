from abc import ABC, abstractmethod
from app.strategies.strategy_state import StrategyState

class BaseWeighting(ABC):

    @abstractmethod
    def generate_weights(self, state : StrategyState) -> dict[str, float]:
        pass