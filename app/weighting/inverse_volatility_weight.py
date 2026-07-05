from app.weighting.base_weighting import BaseWeighting
from app.strategies.strategy_state import StrategyState

class InverseVolatilityWeight(BaseWeighting):
    def __init__(self, indicator : str):
        self.indicator = indicator
        
    

    def generate_weights(self, state : StrategyState) -> dict[str,float]:
        if self.indicator not in state.indicator_results:
            raise ValueError(
                f"Indicator '{self.indicator}' has not been calculated. "
                f"Available indicators: {list(state.indicator_results.keys())}"
            )
        

        volatility = state.indicator_results[self.indicator]

        volatility = volatility.loc[state.selected_tickers]

        inverse_volatility = 1/volatility # This is a pandas series

        weights = inverse_volatility / inverse_volatility.sum() #Inverse Vol of Stock / total

        return weights.to_dict()

        