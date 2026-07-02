from abc import ABC, abstractmethod

class BaseUniverse(ABC):

    @abstractmethod
    def get_tickers(self) -> list[str]:
        pass