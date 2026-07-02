from abc import ABC, abstractmethod
import pandas as pd


#Input historical prices ; Output one value per stock
class BaseIndicator(ABC):

    @property
    @abstractmethod
    def name(self):
        pass
        

    @abstractmethod
    def calculate(self,state):
        pass