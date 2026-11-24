"""Price-only backtest of the trading rules, with real Danish costs, to choose the parameters.

    python research/backtest.py            # needs Yahoo Finance access (run it via GitHub Actions)

What it can and cannot tell you
- It tests the parts that depend only on prices: momentum ranking, the 200-day trend filter,
  number of holdings, rebalance frequency, keep band, whole shares, fees, FX and tax drag.
- It CANNOT test the skill's fundamental score: free data has no point-in-time history of
  statements, and using today's statements on old prices would be look-ahead bias.
- The universe is today's large caps, so returns are flattered by survivorship bias. Use the
  results to compare variants with each other, not as a forecast.
"""
from __future__ import annotations

import itertools
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from trader.costs import CostModel, ask_tax  # noqa: E402

START = "2011-01-01"


def load():
    import yfinance as yf

    uni = json.loads((ROOT / "config/universe.json").read_text())
    tickers = list(uni["tickers"])
    raw = yf.download(tickers + ["SPY", "DKK=X"], start=START, auto_adjust=True, progress=False, threads=True)
    close, opn = raw["Close"], raw["Open"]
    for df in (close, opn):
        df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
    fx = close.pop("DKK=X").ffill()
    opn = opn.drop(columns=["DKK=X"])
    keep = close["SPY"].notna()
    return close[keep].ffill(limit=3), opn[keep], fx.reindex(close.index[keep]).ffill().bfill(), tickers


def simulate(close, opn, fx, tickers, cm: CostModel, n=5, freq="M", band=None, lookback=252, skip=21,
             trend=True, capital=10_000.0, tax=True, park=False, costs=True):
    band = band or n
    dates = close.index
    cash, shares = capital, {}
    vals, costs_paid, traded = [], 0.0, 0.0
    pending = None
    year_start_val, loss_carry = capital, 0.0
    period = (lambda d: (d.year, d.month)) if freq == "M" else (lambda d: (d.year, (d.month - 1) // 3))
    last_period = None
    mom = close[tickers].shift(skip) / close[tickers].shift(lookback) - 1
    sma = close[tickers].rolling(200).mean()
    cmz = cm if costs else CostModel(0, 0, 0, 0, 0, 0, cm.whole_shares, cm.withholding_pct, cm.tax_pct)
    for i, d in enumerate(dates):
        f = float(fx.iloc[i])
        # 1) fill yesterday's orders at today's open
        if pending is not None:
            sells, buys = pending
            for t in sells:
                if t in shares and not math.isnan(opn.at[d, t]):
                    r = cmz.sell(float(opn.at[d, t]), shares.pop(t), "USD", f, 7.46)
                    cash += r["total"]
                    costs_paid += r["fx_fee"] + r["commission"] + r["slippage"]
                    traded += r["gross"]
            val_now = cash + sum(s * float(close.iloc[i - 1][t]) * f for t, s in shares.items())
            for t in buys:
                p = opn.at[d, t]
                if math.isnan(p):
                    continue
                r = cmz.buy(float(p), cash, val_now / n, "USD", f, 7.46)
                if r:
                    shares[t] = shares.get(t, 0) + r["shares"]
                    cash -= r["total"]
                    costs_paid += r["fx_fee"] + r["commission"] + r["slippage"]
                    traded += r["gross"]
            pending = None
        px = close.iloc[i]
        value = cash + sum(s * float(px[t]) * f for t, s in shares.items())
        # 2) ASK tax at the turn of the year (paid from cash; may go briefly negative)
        if tax and i > 0 and d.year != dates[i - 1].year:
            prev = vals[-1]
            t_, loss_carry = ask_tax(prev - year_start_val, loss_carry, cm.tax_pct)
            cash -= t_
            value -= t_
            year_start_val = value
        vals.append(value)
        # 3) decide at the close of the first day of each new period
        if i < lookback or period(d) == last_period:
            continue
        last_period = period(d)
        m = mom.iloc[i].dropna()
        if trend:
            ok = px[m.index] > sma.iloc[i][m.index]
            m = m[ok.fillna(False)]
        ranked = list(m.sort_values(ascending=False).index)
        rank = {t: k + 1 for k, t in enumerate(ranked)}
        keep = [t for t in shares if rank.get(t, 999) <= band]
        sells = [t for t in shares if t not in keep]
        buys = [t for t in ranked if t not in keep][: max(0, n - len(keep))]
        if cash < 0:  # tax overdraft: sell the weakest holding
            sells = list(set(sells) | {min(keep, key=lambda t: rank.get(t, 999))}) if keep else sells
        pending = (sells, buys)
    v = pd.Series(vals, index=dates)
    return v, costs_paid, traded


def stats(v: pd.Series, capital: float, costs_paid: float, traded: float):
    v = v[v.index >= v.index[252]]  # measure after the warm-up
    v = v / v.iloc[0] * capital
    yrs = (v.index[-1] - v.index[0]).days / 365.25
    r = v.pct_change().dropna()
    return {
        "cagr_pct": round(float((v.iloc[-1] / v.iloc[0]) ** (1 / yrs) - 1) * 100, 2),
        "max_drawdown_pct": round(float((v / v.cummax() - 1).min()) * 100, 1),
        "volatility_pct": round(float(r.std()) * math.sqrt(252) * 100, 1),
        "sharpe": round(float(r.mean() / r.std() * math.sqrt(252)), 2),
        "costs_pct_per_year": round(costs_paid / capital / yrs * 100, 2),
        "turnover_x_per_year": round(traded / capital / yrs / 2, 2),
        "years": round(yrs, 1),
        "worst_year_pct": round(float(v.resample("YE").last().pct_change().min() * 100), 1),
    }


def main():
    cm = CostModel.from_config(json.loads((ROOT / "config/broker.json").read_text()))
    close, opn, fx, tickers = load()
    print(f"{len(tickers)} tickers, {close.index[0].date()} to {close.index[-1].date()}")
    results = []
    for capital in (10_000.0, 100_000.0):
        etf_cm = CostModel(**{**cm.__dict__, "whole_shares": False})  # UCITS units are ~EUR 100, near-fractional
        v, c, t = simulate(close, opn, fx, ["SPY"], etf_cm, n=1, freq="Y", band=1, lookback=253, skip=0, trend=False, capital=capital)
        results.append({"name": "S&P 500 ETF, buy and hold", "capital": capital, **stats(v, capital, c, t)})
        for n, freq, band_x, trend, lb in itertools.product((3, 4, 5, 6, 8), ("M", "Q"), (1, 2), (True, False), (252, 126)):
            band = n * band_x
            v, c, t = simulate(close, opn, fx, tickers, cm, n=n, freq=freq, band=band, trend=trend, lookback=lb, capital=capital)
            results.append({"name": f"{n} stocks, {'monthly' if freq == 'M' else 'quarterly'}, keep top {band}, "
                                    f"{'trend filter' if trend else 'no filter'}, {12 if lb == 252 else 6}-1m momentum",
                            "n": n, "freq": freq, "band": band, "trend": trend, "lookback": lb,
                            "capital": capital, **stats(v, capital, c, t)})
        # cost drag reference: best-known config without costs
        v, c, t = simulate(close, opn, fx, tickers, cm, n=5, freq="M", band=10, capital=capital, costs=False)
        results.append({"name": "5 stocks, monthly, keep top 10, NO COSTS (reference)", "capital": capital,
                        **stats(v, capital, c, t)})
        print(f"capital {capital:,.0f}: done")
    out = ROOT / "research"
    (out / "backtest_results.json").write_text(json.dumps({
        "generated": pd.Timestamp.utcnow().isoformat(), "period": [str(close.index[252].date()), str(close.index[-1].date())],
        "universe": tickers, "caveats": __doc__, "results": results}, indent=1))
    df = pd.DataFrame(results)
    lines = ["# Backtest results", "", __doc__.strip(), "",
             f"Period {close.index[252].date()} to {close.index[-1].date()}, values in DKK after Saxo costs and 17% ASK tax.", ""]
    for capital in (10_000.0, 100_000.0):
        sub = df[df.capital == capital].sort_values("sharpe", ascending=False)
        lines += [f"## Starting with {capital:,.0f} kr (sorted by Sharpe)", "",
                  sub[["name", "cagr_pct", "sharpe", "max_drawdown_pct", "worst_year_pct", "costs_pct_per_year", "turnover_x_per_year"]]
                  .head(25).to_markdown(index=False), ""]
    (out / "backtest_results.md").write_text("\n".join(lines))
    print("\n".join(lines[:60]))


if __name__ == "__main__":
    main()
