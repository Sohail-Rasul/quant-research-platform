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
        # FIX: BaseWeighting implementations (EqualWeight, InverseVolatilityWeight)
        # expect a StrategyState with .selected_tickers, not a raw list. This used
        # to call self.weighting.generate_weights(tickers) with a plain list,
        # which crashed with "AttributeError: 'list' object has no attribute
        # 'selected_tickers'" the moment you tried to run the buy-and-hold
        # benchmark - same convention as PipelineStrategy is used here now.
        state.selected_tickers = self.universe.get_tickers()

        return self.weighting.generate_weights(state)
