from app.universe.base_universe import BaseUniverse

class UserUniverse(BaseUniverse):

    def __init__(self, tickers: list[str]):
        self.tickers = tickers

    def get_tickers(self) -> list[str]:
        return self.tickers