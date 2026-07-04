from app.filters.base_filter import BaseFilter
from app.strategies.strategy_state import StrategyState

import operator

OPERATORS = {
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
    "==": operator.eq,
    "!=": operator.ne
}

class ThresholdFilter(BaseFilter):
    def __init__(self,indicator : str , threshold : float, operator : str):
        self.indicator = indicator
        self.threshold = threshold
        self.operator = operator

        if self.operator not in OPERATORS:
            raise ValueError(f"Invalid operator '{self.operator}'."
                            f"Supported operators: {list(OPERATORS.keys())}")

    def apply(self, state : StrategyState):
        indicator_values = state.indicator_results[self.indicator]
        # SAME LOGIC AS TOPNRANKER
        # Only evaluate stocks that survived previous pipeline stages.
        indicator_values = indicator_values.loc[state.selected_tickers]
        

        mask = OPERATORS[self.operator](indicator_values , self.threshold)

        state.selected_tickers = indicator_values[mask].index.tolist() #GIVES ONLY STOCK NAMES WHICH PASSED THRESHOLD IN LIST FORMAT

