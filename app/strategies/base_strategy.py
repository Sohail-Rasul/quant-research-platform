from abc import ABC, abstractmethod

class Strategy(ABC):

    @abstractmethod
    def generate_weights(self):
        pass