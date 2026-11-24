"""Saving 80,000 kr towards a house deposit: how many years until investing beats a savings account?

    python research/horizon.py         # needs Yahoo Finance (Actions -> Backtest, script horizon)

For every horizon from 1 to 10 years, every monthly start since 1993 is tested:
  Savings  2.0% interest a year, taxed at 37% as capital income (best accounts paid ~2.3% with a year's
           binding in autumn 2026; the central bank rate was 2.1%)
  Index    a Danish-listed global/US index fund on an aktiesparekonto (0.40% a year, 0.10% min 29 kr per
           trade at Lån & Spar, 17% tax on each year's gain, losses carried forward)
  Glide    the index fund, moved to savings in equal monthly steps over the final 2 years (final year for
           horizons up to 3 years), so a late crash can only hit part of the money

Index history: S&P 500 (SPY) total return in DKK from 1996 (USD before), the longest free series. US stocks
did unusually well in this period, so the index results are flattering. A range of what happened, not a
forecast. Not investment advice.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from trader.costs import ask_tax  # noqa: E402

CAPITAL = 80_000.0
SAVINGS_NET = 0.020 * (1 - 0.37)
FUND_COST = 0.0040
TRADE = lambda amt: max(0.0010 * amt, 29.0) + 7.5 if amt > 0 else 0.0  # noqa: E731


def load():
    import yfinance as yf

    raw = yf.download(["SPY", "DKK=X"], start="1993-01-01", auto_adjust=True, progress=False)["Close"]
    raw.index = pd.to_datetime(raw.index).tz_localize(None).normalize()
    m = raw.resample("ME").last()
    usd = m["SPY"].pct_change()
    dkk = (m["SPY"] * m["DKK=X"]).pct_change()
    r = dkk.where(dkk.notna(), usd).dropna()  # DKK where the exchange rate exists, USD before
    return r + (0.00095 - FUND_COST) / 12


def simulate(rets: np.ndarray, glide_months: int = 0) -> float:
    """Value in kroner at the end, after all costs and taxes, ready to use as a deposit."""
    n = len(rets)
    inv = CAPITAL - TRADE(CAPITAL)
    cash, withdrawn, year_start, carry = 0.0, 0.0, inv, 0.0
    glide_start = n - glide_months
    for k, r in enumerate(rets, start=1):
        inv *= 1 + r
        cash *= (1 + SAVINGS_NET) ** (1 / 12)
        if glide_months and k > glide_start and inv > 0:
            left = n - k + 1
            amt = inv / left
            inv -= amt
            withdrawn += amt
            cash += amt - TRADE(amt)
        if k % 12 == 0 or k == n:
            tax, carry = ask_tax(inv + withdrawn - year_start, carry, 0.17)
            withdrawn = 0.0
            if tax > 0 and inv >= tax + 40:
                inv -= tax + TRADE(tax)
            else:
                cash -= tax
            year_start = inv
    return cash + inv - TRADE(inv)


def main():
    r = load()
    rows = []
    for years in range(1, 11):
        n = years * 12
        starts = range(0, len(r) - n + 1)
        save = CAPITAL * (1 + SAVINGS_NET) ** years
        for plan, glide in (("Index fund", 0), ("Index fund, glide to savings", 24 if years > 3 else 12 if years > 1 else 0)):
            if plan.startswith("Index fund, glide") and years == 1:
                continue
            outs = np.array([simulate(r.iloc[s:s + n].values, glide) for s in starts])
            rows.append({
                "years": years, "plan": plan, "windows": len(outs), "savings_kr": round(save),
                "median_kr": round(float(np.median(outs))), "worst_10pct_kr": round(float(np.percentile(outs, 10))),
                "worst_kr": round(float(outs.min())),
                "pct_beat_savings": round(float((outs > save).mean() * 100)),
                "pct_below_80k": round(float((outs < CAPITAL).mean() * 100)),
                "pct_lost_over_20pct": round(float((outs < 0.8 * CAPITAL).mean() * 100)),
            })
    df = pd.DataFrame(rows)
    out = ROOT / "research"
    (out / "horizon.json").write_text(json.dumps({"period": [str(r.index[0].date()), str(r.index[-1].date())],
                                                  "notes": __doc__, "rows": rows}, indent=1))
    md = ["# How many years before investing beats saving? (80,000 kr towards a house deposit)", "", __doc__.strip(), "",
          f"Monthly windows from {r.index[0].date()} to {r.index[-1].date()}.", "",
          df[["years", "plan", "windows", "savings_kr", "median_kr", "worst_10pct_kr", "worst_kr", "pct_beat_savings",
              "pct_below_80k", "pct_lost_over_20pct"]].to_markdown(index=False), ""]
    (out / "horizon.md").write_text("\n".join(md))
    print("\n".join(md))


if __name__ == "__main__":
    main()
