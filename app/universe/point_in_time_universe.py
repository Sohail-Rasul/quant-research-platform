from app.universe.base_universe import BaseUniverse
import pandas as pd


class PointInTimeUniverse(BaseUniverse):
    """
    NOT WIRED INTO runner.py BY DEFAULT — this is a building block for fixing
    survivorship bias (audit §4.1), not a complete fix by itself.

    UserUniverse (the current default) always returns the same static ticker
    list for every date, regardless of whether those companies actually
    existed / were index constituents on that historical date. This class
    instead returns only the tickers that were constituents of the index
    on (or before) a given date, based on a membership table you supply.

    WHAT THIS DOES NOT DO:
    It does not, by itself, fix survivorship bias. If a stock was delisted
    or went bankrupt, this class can correctly stop including it after its
    `removed_date` — but only if `prices` for that stock also has a real
    price history up through its last trading day. If your `prices` table
    only contains tickers that still exist today, this class has nothing
    to exclude, because those failed companies were never backfilled in
    the first place. You need BOTH:
      1. a historical constituent membership table (what this class uses), AND
      2. price history for delisted/merged names through their exit date
         (a separate data-sourcing task — see chat for suggestions).

    Usage:
        membership = pd.DataFrame({
            "ticker": ["RELIANCE.NS", "SOMECO.NS", ...],
            "added_date": ["2010-01-01", "2019-06-01", ...],
            "removed_date": [None, "2022-03-15", ...],  # None/NaN = still a member
        })
        universe = PointInTimeUniverse(membership)
        # PipelineStrategy will call universe.set_date(state.date) automatically
        # before get_tickers() on every signal date.
    """

    def __init__(self, membership: pd.DataFrame):
        self.membership = membership.copy()
        self.membership["added_date"] = pd.to_datetime(self.membership["added_date"])
        self.membership["removed_date"] = pd.to_datetime(self.membership["removed_date"])
        self._current_date = None

    def set_date(self, date):
        self._current_date = pd.Timestamp(date)

    def get_tickers(self) -> list[str]:
        if self._current_date is None:
            raise ValueError(
                "PointInTimeUniverse.set_date(date) must be called before get_tickers()."
            )

        m = self.membership

        was_member = (m["added_date"] <= self._current_date) & (
            m["removed_date"].isna() | (m["removed_date"] >= self._current_date)
        )

        return m.loc[was_member, "ticker"].tolist()
