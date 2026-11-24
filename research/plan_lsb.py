"""Backtest plans for 80,000 kr on an aktiesparekonto at Lån & Spar Bank.

    python research/plan_lsb.py        # needs Yahoo Finance (run it via Actions -> Backtest, script plan_lsb)

Lån & Spar online prices (lsb.dk/dine-vilkaar/gebyrlisten, read 24 Nov 2026):
- Danish-listed shares and funds: 0.10%, min 29 kr; 7.50 kr per holding change; no custody fee (VP)
- US and other foreign shares: 0.20%, min 29 kr; currency +/- 1.30 kr per 100 USD (~0.19%)
- Foreign shares held outside VP: 0.25% a year, min 250 kr
Index funds: Danske Invest Global Indeks (MSCI World) costs 0.40% a year, Lån & Spar Invest Globale
Aktier Basis 0.44%. Modelled with iShares MSCI World (URTH, 0.24%) total returns, adjusted to 0.40%.

Same caveats as backtest.py: the stock universe is today's survivors, and the skill's fundamental score
cannot be backtested. Compare plans with each other and with the index fund, not as forecasts.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research"))
from backtest import load, simulate, stats  # noqa: E402
from trader.costs import CostModel, ask_tax  # noqa: E402

CAPITAL = 80_000.0
WARMUP = 252  # every plan starts investing on the same day, after the momentum look-back

LSB_STOCKS = CostModel(
    commission_pct=0.0020, commission_min_usd=0.0, etf_commission_pct=0.0020, etf_commission_min_eur=0.0,
    fx_fee_pct=0.0019, slippage_pct=0.0005, whole_shares=True, withholding_pct=0.15, tax_pct=0.17,
    commission_min_dkk=29.0)
CUSTODY_PCT, CUSTODY_MIN = 0.0025, 250.0


def index_fund(price_dkk: pd.Series, capital: float, fund_cost_pct: float, proxy_cost_pct: float,
               buy_pct: float, buy_min: float, per_trade: float = 0.0, custody_pct: float = 0.0,
               custody_min: float = 0.0, fx_pct: float = 0.0):
    """Buy once on the warm-up day and hold, paying the fund's yearly cost, custody and 17% ASK tax.
    Tax is paid by selling just enough units."""
    dates = price_dkk.index
    rets = price_dkk.pct_change().fillna(0.0) + (proxy_cost_pct - fund_cost_pct) / 252
    vals, invested, cash, costs = [], 0.0, capital, 0.0
    year_start, carry = capital, 0.0
    for i, d in enumerate(dates):
        if i == WARMUP:
            fee = max(buy_pct * cash, buy_min) + per_trade + fx_pct * cash
            invested, cash, costs = cash - fee, 0.0, costs + fee
        elif i > WARMUP:
            invested *= 1 + rets.iloc[i]
        value = invested + cash
        if i > WARMUP and d.year != dates[i - 1].year:
            fee = max(custody_pct * invested, custody_min) if custody_pct else 0.0
            tax, carry = ask_tax(vals[-1] - year_start, carry, 0.17)
            need = fee + tax
            if need > 0:
                sell_fee = max(buy_pct * need, buy_min) + per_trade + fx_pct * need
                invested -= need + sell_fee
                costs += fee + sell_fee
            value = invested + cash
            year_start = value
        vals.append(value)
    return pd.Series(vals, index=dates), costs


def main():
    close, opn, fx, tickers = load(extra=("URTH",))
    world_dkk = (close["URTH"] * fx).ffill()
    spy_dkk = (close["SPY"] * fx).ffill()
    close_s = close.drop(columns=["URTH"])
    opn_s = opn.drop(columns=["URTH"])
    print(f"{close.index[0].date()} to {close.index[-1].date()}")

    runs = {}
    v, c = index_fund(world_dkk, CAPITAL, 0.0040, 0.0024, 0.0010, 29.0, per_trade=7.5)
    runs["Global index fund (Danske Invest Global Indeks, 0.40%)"] = (v, c, 0.0)
    v, c = index_fund(spy_dkk, CAPITAL, 0.0007, 0.0009, 0.0020, 29.0, custody_pct=CUSTODY_PCT,
                      custody_min=CUSTODY_MIN, fx_pct=0.0017)
    runs["S&P 500 UCITS ETF bought at Lån & Spar (foreign, custody fee)"] = (v, c, 0.0)

    for n in (4, 6, 8):
        for custody in (True, False):
            v, c, t = simulate(close_s, opn_s, fx, tickers, LSB_STOCKS, n=n, freq="Q", band=2 * n, trend=False,
                               lookback=WARMUP, capital=CAPITAL,
                               custody_pct=CUSTODY_PCT if custody else 0.0, custody_min=CUSTODY_MIN if custody else 0.0)
            runs[f"Stock strategy, {n} stocks" + ("" if custody else " (no custody fee)")] = (v, c, t)

    v, c, t = simulate(close_s, opn_s, fx, tickers, LSB_STOCKS, n=len(tickers), freq="Y", band=len(tickers),
                       lookback=WARMUP + 1, skip=0, trend=False, capital=CAPITAL, custody_pct=CUSTODY_PCT,
                       custody_min=CUSTODY_MIN)
    runs["Same 38 stocks, equal weight, held (survivorship baseline)"] = (v, c, t)

    for core in (0.8, 0.7):
        idx, ic = index_fund(world_dkk, CAPITAL * core, 0.0040, 0.0024, 0.0010, 29.0, per_trade=7.5)
        sat, sc, st = simulate(close_s, opn_s, fx, tickers, LSB_STOCKS, n=4, freq="Q", band=8, trend=False,
                               lookback=WARMUP, capital=CAPITAL * (1 - core),
                               custody_pct=CUSTODY_PCT, custody_min=CUSTODY_MIN)
        runs[f"{int(core * 100)}% global index fund + {int(round((1 - core) * 100))}% stock strategy (4 stocks)"] = (idx + sat, ic + sc, st)

    rows = []
    for name, (v, c, t) in runs.items():
        s = stats(v, CAPITAL, c, t)
        vv = v[v.index >= v.index[WARMUP]]
        s["end_value_kr"] = round(float(vv.iloc[-1] / vv.iloc[0] * CAPITAL))
        rows.append({"plan": name, **s})
        print(name, s["cagr_pct"], s["max_drawdown_pct"])

    start, end = str(close.index[WARMUP].date()), str(close.index[-1].date())
    out = ROOT / "research"
    (out / "plan_lsb.json").write_text(json.dumps({"period": [start, end], "capital": CAPITAL, "notes": __doc__,
                                                   "rows": rows}, indent=1))
    df = pd.DataFrame(rows)
    md = ["# 80,000 kr on a Lån & Spar aktiesparekonto: plan backtest", "", __doc__.strip(), "",
          f"Invested {start}, measured to {end}. All values in DKK after fees, custody, dividend tax and 17% ASK tax.",
          "The real column is 80,000 kr put in 10 years before the end, in start-month kroner after Danish inflation.", "",
          df[["plan", "cagr_pct", "cagr_2012_2018_pct", "cagr_2019_now_pct", "max_drawdown_pct", "worst_year_pct",
              "costs_pct_per_year", "end_value_kr", "value_of_80k_after_10y_kr", "value_of_80k_after_10y_real_kr"]].to_markdown(index=False)]
    (out / "plan_lsb.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
