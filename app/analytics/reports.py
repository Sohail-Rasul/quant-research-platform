from app.analytics.performance import (calculate_total_return, calculate_cagr, calculate_sharpe, calculate_volatility, calculate_max_drawdown)
import pandas as pd

def generate_results(equity_curve:pd.DataFrame):

    metrics = {
        "total_return": calculate_total_return(equity_curve),
        "cagr": calculate_cagr(equity_curve),
        "volatility": calculate_volatility(equity_curve),
        "sharpe": calculate_sharpe(equity_curve),
        "max_drawdown": calculate_max_drawdown(equity_curve)
    }

    return metrics
    