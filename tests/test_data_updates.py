import sys
import types
from datetime import date

import pandas as pd

import app.update as update_mod


class FakeCursor:
    def __init__(self, log, results):
        self.log, self.results = log, list(results)

    def execute(self, sql, params=None):
        self.log.append(sql)

    def executemany(self, sql, rows):
        self.log.append(sql)

    def fetchone(self):
        return self.results.pop(0)

    def close(self):
        pass


class FakeConn:
    def __init__(self, results):
        self.log, self.results = [], results

    def cursor(self):
        return FakeCursor(self.log, self.results)


def fake_ticker(actions, history):
    return types.SimpleNamespace(actions=actions, history=lambda **k: history)


def hist():
    idx = pd.DatetimeIndex(["2024-01-02"], tz="Asia/Kolkata")
    return pd.DataFrame({"Open": [10.], "High": [11.], "Low": [9.], "Close": [10.], "Adj Close": [10.], "Volume": [100]}, index=idx)


def test_update_appends_when_no_new_corporate_action(monkeypatch):
    actions = pd.DataFrame({"Dividends": [1.0]}, index=pd.DatetimeIndex(["2020-01-01"]))
    monkeypatch.setattr(update_mod.yf, "Ticker", lambda t: fake_ticker(actions, hist()))
    conn = FakeConn([(1,), (date(2023, 12, 1),)])
    assert update_mod.update_prices(conn, "X.NS")
    assert any("DO NOTHING" in q for q in conn.log)


def test_update_overwrites_history_after_new_split(monkeypatch):
    actions = pd.DataFrame({"Stock Splits": [2.0]}, index=pd.DatetimeIndex(["2023-12-20"]))
    import app.backfill as backfill_mod
    t = fake_ticker(actions, hist())
    monkeypatch.setattr(update_mod.yf, "Ticker", lambda x: t)
    monkeypatch.setattr(backfill_mod.yf, "Ticker", lambda x: t)
    conn = FakeConn([(1,), (date(2023, 12, 1),), (1,)])
    assert update_mod.update_prices(conn, "X.NS")
    assert any("DO UPDATE" in q for q in conn.log)       # full refresh, not append
