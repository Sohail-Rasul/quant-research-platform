from app.weighting.base_weighting import BaseWeighting
from app.strategies.strategy_state import StrategyState

class EqualWeight(BaseWeighting):

    def generate_weights(self, state : StrategyState) -> dict[str,float]:
        no_of_tickers = len(state.selected_tickers)
        weights = {}
        if no_of_tickers != 0 : weight = 1 / no_of_tickers
        else: return weights

        

        for ticker in state.selected_tickers:
            weights[ticker] = weight
        
        return weights