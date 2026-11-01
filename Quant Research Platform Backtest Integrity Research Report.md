# Backtesting Indian Equities: What I Built, What Broke and What I Learned

My momentum strategy reported 100%+ CAGR on Indian equities, and I did not trust it. The simulation engine holds up under testing, but the data I fed it flatters the strategy, and most of the headline return was bias. This document records how I tested that, what I found and what I still cannot explain.

## 1. Summary

I built a Python backtester for Indian equities: PostgreSQL data, indicators, a composite factor model, a Top-N ranker, monthly rebalancing and a Streamlit dashboard. Early runs gave CAGRs between 30% and 110%, which looked too good, so I investigated before building anything further.

- **The mechanics are sound.** Signals use only past data, trades execute afterwards, and the return maths is correct. There is no same-day look-ahead.
- **The inputs are biased.** My universe is today’s NSE 500 applied to past dates, and my price history contains no stocks that failed or were delisted. This survivorship bias is the main reason the headline numbers are too high.
- **The 100% CAGR does not survive.** Restricting each rebalance to the 200 most-traded stocks cut CAGR from 99% to 57%. Removing the size tilt took it to about 50%, and even that is an upper bound.
- **Momentum appears to carry real information.** It beat random stock selection by about 52 points of CAGR on the same universe, though that edge is overstated by the same bias.

What is left is mostly a data problem (delisted prices, historical index membership, historical share counts), not a code problem.

## 2. What I built

The project began as a terminal backtest script and is becoming a configurable research dashboard. Before adding research features I wanted results I could trust.

Data flow: PostgreSQL (stocks, prices) → loaders → BacktestEngine → StrategyState → indicators → factor model → filters → ranker → weighting → orders → equity curve → analytics → dashboard.

| Component | How it works |
| --- | --- |
| Universe | 454 stocks ingested from the 504 rows in data/NSE\_500.csv, a snapshot of the NSE 500 list taken when I ingested it (the other tickers failed ingestion) |
| Prices | Daily data from yfinance, stored as adj\_close (split and dividend adjusted) plus raw OHLC and volume, NUMERIC(12,4) |
| Metadata | One row per stock, including a single static shares\_outstanding value |
| Indicators | 63-day momentum, 63-day annualised volatility, size = log(shares × price) |
| Factor model | Cross-sectional z-scores per date; weights momentum 0.6, volatility −0.2, size −0.2 |
| Selection | Top N by composite score (N = 20 in the runs below), monthly rebalance |
| Weighting | Equal weight or inverse volatility |
| Execution | Signal from the previous trading day’s close, trade at the next trading day’s close, proportional transaction cost, whole shares only |
| Entry points | The dashboard and the terminal script both call the same run\_backtest(), so they cannot drift apart |

## 3. How I investigated

I read the code end to end and followed a result from the database to the dashboard. I then wrote 19 automated tests that run on synthetic data with no database, compared the original and fixed code on identical inputs, and ran controlled experiments on my own data, changing one setting at a time.

Two limits apply. The tests have not been run against live data feeds, and everything I know about my database comes from the code and from my own runs.

## 4. What works

| Area | Evidence |
| --- | --- |
| Signal and execution timing | A test records the data each signal sees. It is never later than the signal date, and the first signal is strictly before the first trade. |
| No future-data leakage | A test rewrites all prices after a cutoff date. Every trade before the cutoff is unchanged. |
| Warmup and thin history | Stocks without a full 63-day window get no score. Late IPOs are excluded until they have one. |
| Return maths | CAGR uses actual elapsed days. Volatility, Sharpe and drawdown use standard formulas (Sharpe assumes a 0% risk-free rate). |
| Z-scores | Computed across stocks on each date, not across time. Signs match a momentum, low-volatility, small-size style. |
| Portfolio accounting | After the rebalance fix, cash never goes negative and portfolio value equals cash plus positions. |
| Weights | Inverse-volatility weights sum to 1 and are positive. |
| Data gaps | A missing price day is valued at the last known price and logged, instead of aborting the run. |
| Scale | On synthetic data, 454 stocks over about 1,000 days ran end to end. Engine setup took about 1 second after optimisation (it was about 18). |
| Regression safety | On a 40-stock test, the original and fixed code produced identical CAGR. |

## 5. What I suspected, and what I actually found

### 5.1 Suspected but not wrong

- **Same-day execution look-ahead.** The code already separates the signal date (previous close) from the execution date (next close). Deciding on one close and trading on the next is a legitimate market-on-close convention.
- **CAGR, warmup and z-score direction.** All correct.
- **Dashboard versus terminal discrepancy.** None found.

### 5.2 Bugs I found and fixed

| Bug | Effect | How I found it |
| --- | --- | --- |
| Buy-and-hold benchmark crashed in three separate ways (missing indicators attribute, missing metadata argument, raw list passed to the weighting) | No passive baseline to compare against | Code reading, then a synthetic test exposed the third crash |
| Cash could go negative on rebalance (buys ran before the sells that fund them, and sell-side costs were ignored) | A small amount of free leverage, roughly cost × turnover. It did not change CAGR on typical runs | An automated test. My first review had wrongly concluded no such path existed |
| One missing price day for a held stock aborted the whole run | Fragility | Synthetic edge-case test |
| Dashboard crashed when Run was clicked without dates | Usability | Code reading |
| Z-scores were computed across every loaded stock, not just the investable set | Matters once any universe filter or membership history is used | Design review |
| update\_prices only appended new rows, so after a split or dividend the old stored adj\_close values went stale against the new ones | Could create fake price jumps that corrupt momentum and volatility. Not confirmed in my data | Code reading. The fix was tested with a fake data feed only |
| Backfill let NaN and zero prices through | Data quality | Code reading |
| Transaction cost default of 1 bp was unrealistic and no liquidity filter existed | Flattered returns | Review. Default is now 25 bps and a filter was added |
| requirements.txt incomplete and saved as UTF-16 | Fresh installs failed | Code reading |

### 5.3 A lesson about method

Reading code alone missed two real bugs, the negative cash and the third buy-and-hold crash. Both appeared only when I ran the engine on synthetic data. Automated tests are now part of the project and should grow with it.

## 6. Experiments and results

Setup for all runs: the 454-stock universe, 2020-01-01 to 2024-01-01 (first trade on 2020-04-03), Top 20, inverse-volatility weighting, monthly rebalance. Each run changes one thing from the one before.

| Run | Change | CAGR | Sharpe | Max drawdown |
| --- | --- | --- | --- | --- |
| Baseline | Cost 1 bp, no liquidity filter | 107.76% | 3.12 | −21.42% |
| A | Cost 25 bps | 100.78% | 2.99 | −21.60% |
| B | Plus ₹1 crore/day liquidity floor | 99.27% | 2.96 | −21.59% |
| C | Plus only the 200 most-traded stocks per date | 56.78% | 2.00 | −24.83% |
| D | Plus size weight 0 | 49.71% | 1.88 | −20.36% |

I then ran a bias-check script that compares four portfolios over the same dates (2020-04-03 to 2024-01-01):

| Portfolio | CAGR | Sharpe | Max drawdown |
| --- | --- | --- | --- |
| Strategy (same settings as run B) | 99.27% | 2.96 | −21.59% |
| Random Top 20, five runs (average, range) | 46.82% (37.99% to 51.25%) | n/a | n/a |
| Equal-weight buy-and-hold, 374 stocks | 58.83% | 2.97 | −16.75% |
| Nifty 500 index | 33.29% | 1.91 | −18.48% |

### 6.1 How I read these

- **Costs matter little here.** Going from 1 bp to 25 bps removed about 7 points.
- **The rupee liquidity floor did almost nothing** (1.5 points). A plausible reason is that low-priced, heavily traded stocks clear a rupee-value floor easily. This is an inference, not something I checked in the data.
- **Restricting to the 200 most-traded stocks per date was the big drop**, from 99% to 57%. About 43 points of CAGR came from stocks outside the 200 most-traded on each date.
- **Removing the size tilt cost another 7 points.** Part of this may be a real small-cap premium and part may be the size factor’s flawed share-count data. These runs cannot separate the two.
- **Buy-and-hold beat the index by 25.5 points.** Simply owning today’s index members earned far more than the index did over the same period. This is the survivorship signature, though not all of it (see caveats).
- **The strategy beat random picks by about 52 points.** The factor ranking adds a great deal over random selection on this universe.
- **The strategy matched run B exactly**, so the dashboard and the script agree.

### 6.2 Caveats on these comparisons

- The buy-and-hold portfolio is equal-weight and small/mid-cap heavy, while the index is cap-weighted and large-cap heavy. Small and mid caps rallied strongly in 2020–2024, so some of the gap is style, not survivorship.
- The index series appears to be a price index, so it excludes dividends.
- Only 374 of the 454 stocks had prices on the start date. The other 80 listed later or have missing early data.
- I ran only five random portfolios and one start date.
- The random comparison used the run B settings, not the more restricted run D settings, so it is not an exact like-for-like comparison with run D.

## 7. The main problem: survivorship bias

### 7.1 What it is

There are two separate flaws, and fixing one does not fix the other.

1. **Hindsight membership.** My universe is today’s NSE 500 applied to every past date. A stock that only grew into the index in 2022 is treated as investable in 2020.
2. **Missing losers.** Companies that were delisted, merged or collapsed since 2020 have no rows in my prices table, so the model can never buy them and never takes their losses.

### 7.2 Why I have it

- The universe comes from data/NSE\_500.csv, a snapshot taken when I ingested the data.
- My price loader asks yfinance for the history of each ticker in that snapshot. Delisted tickers are generally not available there. This is my understanding and I have not tested it.
- My schema had no index-membership table and no way to represent a stock whose data ends.
- shares\_outstanding is a single static value per stock, overwritten on each refresh, so history cannot be reconstructed.

### 7.3 Why a momentum strategy is especially exposed

Momentum buys what has recently risen. Take a stock that surged in 2021 and collapsed in 2022. In a real backtest the model would have bought it on the way up and taken the loss. In my universe the stock is missing if it later left the index, so the loss never happens. Only the surviving winners are left to buy, which overstates the payoff of chasing momentum. Volatile, low-priced stocks are the most affected, because they have the highest chance of both spectacular gains and eventual failure.

### 7.4 Evidence

| Observation | What it suggests | Status |
| --- | --- | --- |
| Buy-and-hold on today’s members beat the index by 25.5 points | Survivor or style effect on the universe | Observed, but partly confounded by equal-weight small-cap style |
| Restricting to the 200 most-traded stocks cut CAGR from 99% to 57% | The return leaned on the less-traded part of the universe | Observed |
| The strategy picks many very volatile names (for example TTML, JPPOWER, RPOWER, SUZLON, IDEA, OLECTRA, HINDCOPPER) | Heavy exposure to the stocks most prone to survivorship distortion | Names observed in my logs. I have not checked their 2020 prices or index status |
| Eligible stock count rose from about 350 to about 430 over the backtest | The universe composition changes with listing history | Observed |
| The size of the true bias | Unknown | Cannot be measured without delisted and historical membership data |

## 8. Other problems and why they exist

| Problem | Why it exists | Effect |
| --- | --- | --- |
| Period effect | The first trade is on 2020-04-03, days after the COVID low, and the window ends in a strong small and mid-cap rally | Much of any long-only return here is market beta. Not yet tested with a later start |
| Size factor uses today’s share count | My schema stores one shares\_outstanding value per stock. Splits, bonuses, buybacks and rights issues change the true historical count | Size scores are wrong for past dates. The factor weight is only −0.2, but run D suggests it is not negligible |
| Liquidity filter is ineffective on penny stocks | It filters on rupee traded value, with no minimum price | Low-priced, very active stocks pass |
| Flat transaction cost | One proportional cost applies to every stock | Understates the cost of trading small or illiquid names. No market impact is modelled |
| Delisting loss is unknowable | Real delistings often end well below the last traded price, and no single loss figure is defensible | Needs a sensitivity grid. The current default of zero is optimistic |
| Single in-sample window | I have tested only one period | No evidence the result holds out of sample |
| Sharpe uses a 0% risk-free rate | Simplification | Sharpe is somewhat overstated |
| Stored prices not yet checked for artificial jumps | I have not yet run a check for stale adjusted prices | Possible fake jumps remain unknown |
| Positions table showed 10 names with N = 20 | Possibly just a scrolling table, not confirmed | Open question |

## 9. Possible solutions

| Solution | Fixes | Needs | Effort | Status |
| --- | --- | --- | --- | --- |
| Minimum price filter (for example ₹50) | Penny-stock exposure | Nothing new | Low | Not built |
| Bias-check script that shares the same restrictions as the strategy (K, size weight, start date) | Cleaner attribution of the factor edge | Nothing new | Low | Not built |
| Start-date sensitivity (for example 2021-01-01) | Period effect | Nothing new | None | Not run |
| Point-in-time liquid universe (K most-traded per date) | Part of the hindsight membership | Nothing new | Done | Built |
| Historical index membership | Hindsight membership | A table of added and removed dates. Forum reports say NSE published monthly constituent files for April 2013 to March 2022, but this needs verifying. Otherwise rebuild from semi-annual rebalance announcements or buy from a vendor | Medium to high | Code ready, data missing |
| Prices for delisted stocks | Missing losers | NSE daily bhavcopy archives (unadjusted, so corporate-action data is needed) or a paid vendor. Formats and URLs must be checked | High | Engine rule built, data missing |
| Delisting loss sensitivity | Optimistic delisting treatment | Delisted data first | Low once data exists | Built |
| Historical shares outstanding | Size factor | Corporate-action history or a vendor | Medium | Not built. Interim option: drop the size factor |
| Out-of-sample or walk-forward testing | Overfitting | Nothing new | Medium | Not built |
| Total-return index benchmark and a risk-free rate | Fairer comparisons | Data | Low to medium | Not built |

Free data will probably leave some residual survivorship bias even after all of this. A reasonable standard is to report results as a range and to call them an upper bound until delisted stocks are included.

## 10. What I learned

- **A spectacular result is a reason to investigate, not a verdict.** I traced the data flow instead of assuming the number was wrong, and that is how I separated sound mechanics from biased inputs.
- **Data quality mattered more than code quality.** The engine was largely correct. The biggest distortion came from which stocks I loaded.
- **Reading code is not enough.** Running the engine on synthetic data found two bugs that review missed.
- **Baselines make a result interpretable.** Random picks, buy-and-hold and the index told me more than the strategy’s own numbers did.
- **Change one variable at a time.** The A to D sequence showed exactly where the return came from.
- **Report upper bounds honestly.** Until delisted stocks are in the data, my numbers are ceilings, not estimates.
- **Momentum is especially sensitive to survivorship.** Chasing winners looks best when the losers are missing.

## 11. What I can and cannot claim

| Claim | Supported? |
| --- | --- |
| The backtest mechanics are trustworthy | Yes, verified by tests and code review |
| 100% or 107% CAGR is achievable | No |
| About 50% CAGR (run D) | An upper bound, not an estimate |
| Momentum carries information | Probably, since it beat random picks. The magnitude is overstated |
| Transaction costs explain the high return | No. They changed CAGR by about 7 points |
| The size factor helps | Unclear, because its inputs are wrong |

## 12. Limitations

- Everything I know about my database comes from the code and the results I ran myself.
- The automated tests use synthetic data. The corporate-action refresh logic was tested only against a fake data feed.
- Statements about yfinance, NSE data availability and forum reports are unverified.
- Observations about specific stocks come from my pick lists, not from checks of their historical prices or index status.
- All results come from one configuration and one time window.

## Appendix: files and commands

| Item | Purpose |
| --- | --- |
| tests/ | 19 automated tests, no database needed |
| app/filters/top\_liquidity\_filter.py | Keeps the K most-traded stocks per date |
| app/filters/liquidity\_filter.py | Minimum average traded value |
| app/universe/point\_in\_time\_universe.py | Uses index membership history |
| app/ranking/random\_ranker.py | Random-picks baseline |
| sql/003\_create\_index\_membership.sql and scripts/stocks\_metadata/import\_membership.py | Store and import membership history |
| scripts/backtests/run\_bias\_checks.py | Strategy versus random versus buy-and-hold versus index |
| scripts/stocks\_prices/refresh\_all\_prices.py | One-time rebuild of adjusted prices |

Commands, run from the project root:

- `python -m pytest tests`
- `streamlit run dashboard/dashboard.py`
- `python -m scripts.backtests.run_bias_checks`
- `python -m scripts.stocks_prices.refresh_all_prices`
- `python -m scripts.stocks_metadata.import_membership membership.csv`
