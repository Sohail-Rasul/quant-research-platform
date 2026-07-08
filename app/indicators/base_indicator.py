from abc import ABC, abstractmethod

#Input historical prices ; Output one value per stock
class BaseIndicator(ABC):

    @property
    @abstractmethod
    def name(self):
        pass
        

    @abstractmethod
    def calculate(self,state):
        pass

    @property
    def warmup_period(self) -> int:
        pass