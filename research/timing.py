"""Should you wait for a crash, or ease in? 80,000 kr towards a house in 5 years.

    python research/timing.py          # needs Yahoo Finance (Actions -> Backtest, script timing)

Every monthly start since 1993, 5-year horizon, S&P 500 total return in DKK (same fund costs, Lån & Spar
trading costs and 17% ASK tax as horizon.py; uninvested money earns 2% taxed at 37%):
  All at once     invest the 80,000 kr in month 1
  Over 6 months   invest 1/6 each month, the rest waits in savings
  Over 12 months  invest 1/12 each month
  Savings only    for reference

Each plan is also split by the starting situation: starts right after the market had fallen 10% or more from
its high (like November 2026), and all other starts. Not a forecast. Not investment advice.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research"))
from horizon import CAPITAL, SAVINGS_NET, TRADE  # noqa: E402
from trader.costs import ask_tax  # noqa: E402

YEARS = 5


def load():
    import yfinance as yf

    raw = yf.download(["SPY", "DKK=X"], start="1993-01-01", auto_adjust=True, progress=False)["Close"]
    raw.index = pd.to_datetime(raw.index).tz_localize(None).normalize()
    m = raw.resample("ME").last()
    level = m["SPY"] * m["DKK=X"].where(m["DKK=X"].notna(), 1.0)
    usd = m["SPY"].pct_change()
    dkk = (m["SPY"] * m["DKK=X"]).pct_change()
    r = dkk.where(dkk.notna(), usd).dropna() + (0.00095 - 0.0040) / 12
    drawdown = (m["SPY"] / m["SPY"].cummax() - 1).reindex(r.index)  # in USD terms, like the headlines
    return r, drawdown


def simulate(rets: np.ndarray, spread_months: int) -> float:
    inv, cash = 0.0, CAPITAL
    withdrawn, year_start, carry = 0.0, 0.0, 0.0
    per = CAPITAL / spread_months if spread_months else 0.0
    for k, r in enumerate(rets, start=1):
        if spread_months and k <= spread_months:
            amt = min(per, cash)
            cash -= amt
            inv += amt - TRADE(amt)
            year_start += amt - TRADE(amt)
        inv *= 1 + r
        cash *= (1 + SAVINGS_NET) ** (1 / 12)
        if k % 12 == 0 or k == len(rets):
            tax, carry = ask_tax(inv + withdrawn - year_start, carry, 0.17)
            if tax > 0 and inv >= tax + 40:
                inv -= tax + TRADE(tax)
            else:
                cash -= tax
            year_start = inv
    return cash + inv - TRADE(inv)


def main():
    r, dd = load()
    n = YEARS * 12
    starts = list(range(0, len(r) - n + 1))
    after_drop = np.array([dd.iloc[s - 1] <= -0.10 if s > 0 else False for s in starts])
    save = CAPITAL * (1 + SAVINGS_NET) ** YEARS
    rows = []
    for plan, spread in (("All at once", 1), ("Over 6 months", 6), ("Over 12 months", 12)):
        outs = np.array([simulate(r.iloc[s:s + n].values, spread) for s in starts])
        for label, mask in (("All starts", np.ones(len(starts), bool)), ("Starts after a 10%+ fall", after_drop),
                            ("Other starts", ~after_drop)):
            o = outs[mask]
            rows.append({"plan": plan, "starts": label, "windows": int(mask.sum()), "median_kr": round(float(np.median(o))),
                         "worst_10pct_kr": round(float(np.percentile(o, 10))), "worst_kr": round(float(o.min())),
                         "pct_beat_savings": round(float((o > save).mean() * 100)),
                         "pct_below_80k": round(float((o < CAPITAL).mean() * 100))})
        if plan == "All at once":
            lump = outs
        else:
            rows[-3]["pct_lump_sum_did_better"] = round(float((lump > outs).mean() * 100))
    df = pd.DataFrame(rows)
    out = ROOT / "research"
    (out / "timing.json").write_text(json.dumps({"savings_kr": round(save), "notes": __doc__, "rows": rows}, indent=1))
    md = ["# Wait, ease in, or invest now? 80,000 kr, 5 years", "", __doc__.strip(), "",
          f"Savings only ends at {save:,.0f} kr. Monthly starts {r.index[0].date()} to {r.index[-n].date()}.", "",
          df.to_markdown(index=False), ""]
    (out / "timing.md").write_text("\n".join(md))
    print("\n".join(md))


if __name__ == "__main__":
    main()
