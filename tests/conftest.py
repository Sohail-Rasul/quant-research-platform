import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# app.data.loaders opens a PostgreSQL connection at import time. Tests must not
# need a database, so replace it with a stub whose functions tests can override.
stub = types.ModuleType("app.data.loaders")
for name in ("load_prices", "load_metadata", "load_all_tickers", "load_membership"):
    setattr(stub, name, lambda *a, **k: None)
sys.modules["app.data.loaders"] = stub

# yfinance is only used by the ingestion code; stub it so tests run offline.
yf = types.ModuleType("yfinance")
yf.Ticker = lambda *a, **k: None
sys.modules.setdefault("yfinance", yf)
