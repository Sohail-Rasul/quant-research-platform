from app.strategies.base_strategy import Strategy
from app.universe.base_universe import BaseUniverse
from app.weighting.base_weighting import BaseWeighting
from app.strategies.strategy_state import StrategyState

class BuyAndHoldStrategy(Strategy):
    def __init__(self,universe:BaseUniverse,weighting : BaseWeighting):
            super().__init__()

            if not universe.get_tickers():
                raise ValueError("Universe cannot be empty.")

            self.universe = universe
            self.weighting = weighting

            

    def generate_weights(self, state: StrategyState):
        tickers = self.universe.get_tickers()
        
        return self.weighting.generate_weights(tickers)
