import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

def plot_equity_curve(results : pd.DataFrame):
    x=results["date"]
    y=results["portfolio_value"]

    plt.figure(figsize=(12,6))
    plt.plot(x,y,linewidth = 2)
    plt.grid(True)

    plt.title("Equity Curve")
    plt.xlabel("Date")
    plt.ylabel("Portfolio Value")

    plt.tight_layout()
    plt.show()

def plot_drawdown(results : pd.DataFrame):
    portfolio = results["portfolio_value"]
    running_max = portfolio.cummax()

    drawdown = (portfolio/running_max)-1
    x=results["date"]

    plt.figure(figsize=(12,6))
    plt.plot(x,drawdown,linewidth = 2)
    plt.grid(True)

    plt.title("Drawdown")
    plt.xlabel("Date")
    plt.ylabel("Drawdown")

    plt.axhline(
        y=0,
        linestyle="--"
    )
    plt.gca().yaxis.set_major_formatter(
        mtick.PercentFormatter(1.0)
    )
    
    plt.tight_layout()
    plt.show()