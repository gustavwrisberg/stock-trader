"""80,000 kr and a 5-year goal: pay off the house. Invest on an aktiesparekonto, or pay down the loan?

    python research/house_5y.py        # needs Yahoo Finance (Actions -> Backtest, script house_5y)

Every 5-year window starting each month since 1993 is tested for these plans:
  A  Pay down the mortgage now: a guaranteed return equal to the loan's interest + contribution fee after
     the ~33% interest deduction.
  B  100% global/US index fund on the aktiesparekonto for 5 years (Danish-listed fund, 0.40% a year,
     Lån & Spar: 0.10% min 29 kr per trade, 17% ASK tax each year with losses carried forward).
  C  Half and half: 40,000 kr off the loan now, 40,000 kr in the index fund.
  D  Index fund, then de-risk: sell a third at the start of years 4 and 5 and the rest at the end,
     each sale going straight onto the loan (so it earns the loan rate from then on).
  E  Index fund with a stop: sell everything and pay down the loan once the account is up 25% after tax.

Index data: SPY (S&P 500) total return from 1993, and iShares MSCI World (URTH) from 2012, converted to
DKK where the exchange rate exists. US stocks did unusually well in this period, so B's history is
flattering. Results are a range of what happened, not a forecast. Not investment advice.
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
YEARS = 5
FUND_COST = 0.0040
TRADE = lambda amt: max(0.0010 * amt, 29.0) + 7.5  # Lån & Spar, Danish-listed fund  # noqa: E731
LOAN_RATES = {"3.0% (F3/F5 + fee)": 0.030, "3.8% (F5 + fee)": 0.038, "4.6% (fixed + fee)": 0.046}
DEDUCTION = 0.33


def load():
    import yfinance as yf

    raw = yf.download(["SPY", "URTH", "DKK=X"], start="1993-01-01", auto_adjust=True, progress=False)["Close"]
    raw.index = pd.to_datetime(raw.index).tz_localize(None).normalize()
    m = raw.resample("ME").last()
    fx = m["DKK=X"]
    out = {}
    for name, t, proxy_cost in (("S&P 500 (1993-)", "SPY", 0.00095), ("MSCI World (2012-)", "URTH", 0.0024)):
        p = m[t].dropna()
        dkk = (p * fx.reindex(p.index)).dropna()
        series = dkk if len(dkk) > 0.8 * len(p) else p  # use DKK where the exchange-rate history covers it
        r = series.pct_change().dropna() + (proxy_cost - FUND_COST) / 12
        out[name] = r
    return out


def run_index(rets: pd.Series, capital: float, loan_rate_net: float, sell_plan=None, stop_gain=None):
    """Monthly simulation of a fund on the ASK. sell_plan: {month_index: fraction_of_current_to_sell}.
    Money taken out goes onto the loan and compounds at the loan's after-tax rate. ASK tax is 17% of the
    year's gain including what was taken out during the year (gain = end value + withdrawals - start)."""
    inv = capital - TRADE(capital)
    paid_down, withdrawn = 0.0, 0.0
    year_start, carry = inv, 0.0

    def settle_tax(end_value):
        nonlocal carry, year_start, withdrawn
        tax, carry = ask_tax(end_value + withdrawn - year_start, carry, 0.17)
        withdrawn = 0.0
        return tax

    for k, r in enumerate(rets.values, start=1):
        inv *= 1 + r
        paid_down *= (1 + loan_rate_net) ** (1 / 12)
        frac = (sell_plan or {}).get(k)
        if stop_gain is not None and inv >= capital * (1 + stop_gain):
            frac, stop_gain = 1.0, None
        if frac and inv > 0:
            amt = inv * frac
            inv -= amt
            withdrawn += amt
            paid_down += amt - TRADE(amt)
        if k % 12 == 0:  # ASK tax at each year end
            tax = settle_tax(inv)
            if tax > 0 and inv >= tax + 40:
                inv -= tax + TRADE(tax)
            elif tax > 0:  # account (nearly) emptied: the tax comes out of the money already on the loan
                paid_down -= tax
            year_start = inv
    if inv > 0:  # end of year 5 falls on a year end here, so this only catches a partial year
        tax = settle_tax(inv)
        paid_down += inv - tax - TRADE(inv)
    return paid_down


def main():
    data = load()
    n = YEARS * 12
    rows, windows_info = [], {}
    for idx_name, rets in data.items():
        starts = range(0, len(rets) - n + 1)
        windows_info[idx_name] = [str(rets.index[0].date()), str(rets.index[-1].date()), len(starts)]
        for loan_name, rate in LOAN_RATES.items():
            net = rate * (1 - DEDUCTION)
            loan_value = CAPITAL * (1 + net) ** YEARS
            plans = {
                "A  Pay down the loan now": lambda w: loan_value,
                "B  Index fund for 5 years": lambda w: run_index(w, CAPITAL, net),
                "C  Half loan, half index fund": lambda w: CAPITAL / 2 * (1 + net) ** YEARS + run_index(w, CAPITAL / 2, net),
                "D  Index fund, sell down in years 4-5": lambda w: run_index(w, CAPITAL, net, sell_plan={36: 1 / 3, 48: 1 / 2}),
                "E  Index fund, cash out at +25%": lambda w: run_index(w, CAPITAL, net, stop_gain=0.25),
            }
            for plan, fn in plans.items():
                outs = np.array([fn(rets.iloc[s:s + n]) for s in starts])
                rows.append({
                    "index": idx_name, "loan": loan_name, "plan": plan,
                    "median_kr": round(float(np.median(outs))), "worst_10pct_kr": round(float(np.percentile(outs, 10))),
                    "worst_kr": round(float(outs.min())), "best_kr": round(float(outs.max())),
                    "pct_windows_beat_paydown": round(float((outs > loan_value + 1).mean() * 100)),
                    "pct_windows_below_80k": round(float((outs < CAPITAL).mean() * 100)),
                    "paydown_benchmark_kr": round(loan_value),
                })
    out = ROOT / "research"
    (out / "house_5y.json").write_text(json.dumps({"windows": windows_info, "notes": __doc__, "rows": rows}, indent=1))
    df = pd.DataFrame(rows)
    md = ["# 80,000 kr, 5 years, paying off a house: what actually happened", "", __doc__.strip(), "",
          "Values are the debt removed after 5 years, in kroner, compared like for like: money put on the loan counts",
          "at its interest saved after the deduction. Windows: " + "; ".join(f"{k}: {v[2]} windows, {v[0]} to {v[1]}" for k, v in windows_info.items()), ""]
    for (idx_name, loan_name), sub in df.groupby(["index", "loan"], sort=False):
        md += [f"## {idx_name}, loan rate {loan_name}", "",
               sub[["plan", "median_kr", "worst_10pct_kr", "worst_kr", "best_kr", "pct_windows_beat_paydown",
                    "pct_windows_below_80k"]].to_markdown(index=False), ""]
    (out / "house_5y.md").write_text("\n".join(md))
    print("\n".join(md))


if __name__ == "__main__":
    main()
