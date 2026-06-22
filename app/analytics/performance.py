import pandas as pd
import numpy as np

def calculate_total_return(equity_curve : pd.DataFrame) -> float:
    initial_value = equity_curve["portfolio_value"].iloc[0]
    final_value = equity_curve["portfolio_value"].iloc[-1]

    total_return = (final_value/initial_value)-1
    return total_return


def calculate_cagr(equity_curve: pd.DataFrame) -> float:
    initial_value = equity_curve["portfolio_value"].iloc[0]
    final_value = equity_curve["portfolio_value"].iloc[-1]

    start_date = equity_curve["date"].iloc[0]
    end_date = equity_curve["date"].iloc[-1]

    years = (end_date - start_date).days / 365.25

    cagr = ((final_value/initial_value)**(1/years)) - 1

    return cagr

def calculate_volatility(equity_curve: pd.DataFrame) -> float:
    returns = equity_curve["portfolio_value"].pct_change()
    daily_vol = returns.std()

    annual_vol = (daily_vol)*(np.sqrt(252))

    return annual_vol

def calculate_sharpe(equity_curve: pd.DataFrame) -> float:
    returns = equity_curve["portfolio_value"].pct_change().dropna()
    mean_return = returns.mean()
    volatility = returns.std()

    sharpe = (mean_return/volatility) * np.sqrt(252)

    return sharpe

def calculate_max_drawdown(equity_curve:pd.DataFrame) -> float:
    portfolio = equity_curve["portfolio_value"]
    running_max = portfolio.cummax()

    drawdown = (portfolio/running_max)-1
    max_drawdown = drawdown.min()

    return max_drawdown
