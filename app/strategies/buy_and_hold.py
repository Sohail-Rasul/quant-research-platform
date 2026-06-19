from app.strategies.base_strategy import Strategy

class BuyAndHoldStrategy(Strategy):
    def __init__(self,tickers: list[str]):
        super().__init__()

        self.tickers = tickers

        if not tickers:
            raise ValueError(
                "At least one ticker must be provided."
            )

    def generate_weights(self):
        ticker_weights={}
        
        num_of_stocks = len(self.tickers)
        weight = 1/num_of_stocks

        for ticker in self.tickers:
            ticker_weights[ticker] = weight

        return ticker_weights