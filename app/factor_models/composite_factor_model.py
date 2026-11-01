from app.factor_models.base_factor_model import BaseFactorModel
from app.strategies.strategy_state import StrategyState
from app.utils.statistics import calculate_zscore

class CompositeFactorModel(BaseFactorModel):
    def __init__(self, factor_weights : dict[str,float]):
        self.factor_weights = factor_weights

        if not factor_weights:
            raise ValueError("At least one factor is required.")

    def calculate(self, state : StrategyState):
        # Get indicator results: "momentum" : .... ; "volatility": ....
        indicator_results = state.indicator_results
        composite_score = 0

        # Normalize each factor and accumulate its weighted contribution.
        for indicator_name, weight in self.factor_weights.items():
            # FIX: z-scores must be computed across the stocks that are actually
            # investable on this date (state.selected_tickers: the point-in-time
            # universe after universe filters), NOT across every ticker that
            # happens to be loaded. Otherwise stocks that were not members/liquid
            # on this date still shift the mean and std that everyone is scored
            # against. With no universe filters this is identical to before.
            series = indicator_results[indicator_name].reindex(state.selected_tickers)
            values = calculate_zscore(series) # Calculate ZScore Value (Normalized Value) for each indicator
            composite_score += weight * values # Add to composite score

        state.indicator_results["composite"] = composite_score # Add Composite value along with other indicators and use that for future steps
            
