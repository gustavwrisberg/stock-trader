"""A paper portfolio that behaves like a real Saxo aktiesparekonto.

Timeline of one daily run, after the US close on day T:
  1. splits and dividends since the last run are applied (dividends net of 15% US withholding)
  2. orders decided at an earlier close fill at the OPEN of the next trading day (never the
     close they were decided on: that would be trading on information you could not act on)
  3. on the first run of a new year, 17% ASK tax on last year's gain is paid from cash
  4. the portfolio is valued at T's close
  5. new orders are decided and queued for the next open
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

import pandas as pd

from trader.costs import CostModel, ask_tax

COST_KEYS = ("commission", "fx_fee", "slippage", "withholding", "tax")


def new_portfolio(cash_dkk: float, as_of: str) -> Dict[str, Any]:
    return {"cash": cash_dkk, "positions": {}, "pending": [], "started": as_of, "last_run": None,
            "last_period": None, "year": int(as_of[:4]), "year_start_value": cash_dkk, "loss_carry": 0.0,
            "costs": {k: 0.0 for k in COST_KEYS}, "dividends_net": 0.0, "deposits": cash_dkk}


class Market:
    """Price access for one run: raw Open/Close, dividends, splits, FX to DKK."""

    def __init__(self, opn: pd.DataFrame, close: pd.DataFrame, divs: pd.DataFrame, splits: pd.DataFrame,
                 fx_usd: pd.Series, fx_eur: pd.Series, ccy: Dict[str, str]):
        self.opn, self.close, self.divs, self.splits = opn, close, divs, splits
        self.fx = {"USD": fx_usd, "EUR": fx_eur, "DKK": None}
        self.ccy = ccy

    def rate(self, ccy: str, day) -> float:
        if ccy == "DKK":
            return 1.0
        s = self.fx[ccy]
        s = s[s.index <= day].dropna()
        return float(s.iloc[-1])

    def price(self, frame: pd.DataFrame, t: str, day) -> Optional[float]:
        if t not in frame.columns or day not in frame.index:
            return None
        v = frame.at[day, t]
        return None if v is None or (isinstance(v, float) and math.isnan(v)) else float(v)

    def last_close(self, t: str, day) -> Optional[float]:
        if t not in self.close.columns:
            return None
        s = self.close[t]
        s = s[s.index <= day].dropna()
        return float(s.iloc[-1]) if len(s) else None


def value(p: Dict[str, Any], mk: Market, day) -> float:
    v = p["cash"]
    for t, pos in p["positions"].items():
        px = mk.last_close(t, day) or pos.get("last_price", 0)
        v += pos["shares"] * px * mk.rate(mk.ccy.get(t, "USD"), day)
    return v


def _book(p, r: Dict[str, float]):
    for k in ("commission", "fx_fee", "slippage"):
        p["costs"][k] += r.get(k, 0.0)


def apply_corporate_actions(p: Dict[str, Any], mk: Market, since, until) -> List[Dict[str, Any]]:
    """Splits multiply shares; dividends (ex-date in (since, until]) are paid on shares held before
    that day's open. Returns ledger events."""
    events = []
    for t, pos in p["positions"].items():
        ccy = mk.ccy.get(t, "USD")
        if t in mk.splits.columns:
            sp = mk.splits[t]
            sp = sp[(sp.index > since) & (sp.index <= until) & (sp > 0)]
            for d, ratio in sp.items():
                pos["shares"] = pos["shares"] * float(ratio)
                pos["entry_price"] = pos["entry_price"] / float(ratio)
                events.append({"date": d.strftime("%Y-%m-%d"), "ticker": t, "action": "SPLIT",
                               "reason": f"{ratio:g}-for-1 split: now {pos['shares']:g} shares"})
        if t in mk.divs.columns and ccy == "USD":
            dv = mk.divs[t]
            dv = dv[(dv.index > since) & (dv.index <= until) & (dv > 0)]
            for d, amt in dv.items():
                r = _credit_dividend(p, pos["shares"] * float(amt), mk.rate(ccy, d))
                events.append({"date": d.strftime("%Y-%m-%d"), "ticker": t, "action": "DIVIDEND",
                               "value": round(r["net"], 2), "fee": round(r["withholding"] + r["fx_fee"], 2),
                               "reason": f"${amt:.4f} x {pos['shares']:g} shares, 15% US tax withheld"})
    return events


_CM: Optional[CostModel] = None


def set_cost_model(cm: CostModel):
    global _CM
    _CM = cm


def _credit_dividend(p, amount_usd, fx):
    r = _CM.dividend(amount_usd, fx)
    p["cash"] += r["net"]
    p["dividends_net"] += r["net"]
    p["costs"]["withholding"] += r["withholding"]
    p["costs"]["fx_fee"] += r["fx_fee"]
    return r


def fill_pending(p: Dict[str, Any], mk: Market, label: str) -> List[Dict[str, Any]]:
    """Fill orders at the open of the first trading day after they were placed. Sells first, then
    the day's buys are sized together: whole shares within each budget, then leftover cash buys one
    more share at a time for the most under-filled position (at most 30% over budget). Extra shares
    ride on the same order, so they add no extra minimum commission."""
    trades, keep, buys = [], [], []
    for o in sorted(p["pending"], key=lambda o: o["side"]):  # sells (-1) first
        t, ccy = o["ticker"], mk.ccy.get(o["ticker"], "USD")
        days = [d for d in mk.opn.index[mk.opn.index > pd.Timestamp(o["placed"])] if mk.price(mk.opn, t, d) is not None]
        if not days:
            keep.append(o)  # market has not opened for this order yet
            continue
        d = days[0]
        px, fx, eur = mk.price(mk.opn, t, d), mk.rate(ccy, d), mk.rate("EUR", d)
        if o["side"] < 0:
            pos = p["positions"].get(t)
            if not pos:
                continue
            n_sell = min(o.get("shares") or pos["shares"], pos["shares"])
            r = _CM.sell(px, n_sell, ccy, fx, eur)
            p["cash"] += r["total"]
            _book(p, r)
            part_cost = pos["cost_dkk"] * n_sell / pos["shares"]
            pnl_pct = (r["total"] / part_cost - 1) * 100 if part_cost else 0.0
            pos["shares"] -= n_sell
            pos["cost_dkk"] -= part_cost
            if pos["shares"] <= 0:
                del p["positions"][t]
            trades.append(_trade(label, d, t, "SELL", r, ccy, o["reason"] + f" ({pnl_pct:+.1f}% after all costs)"))
        else:
            buys.append((o, d, px, ccy, fx, eur))

    # size buys: whole shares within budget first
    plan = []
    cash = p["cash"]
    for o, d, px, ccy, fx, eur in buys:
        r = _CM.buy(px, cash, o["budget_dkk"], ccy, fx, eur)
        n = r.get("shares", 0) if r else 0
        plan.append([o, d, px, ccy, fx, eur, n])
        if r:
            cash -= r["total"]

    def cost(item, n):
        _, _, px, ccy, fx, eur, _ = item
        return _CM.buy_receipt(px, n, ccy, fx, eur)["total"] if n > 0 else 0.0

    # then spend leftover cash one share at a time on the most under-filled buy
    total_cost = sum(cost(it, it[6]) for it in plan)
    leftover = p["cash"] - total_cost
    while plan:
        best, best_fill = None, 9e9
        for it in plan:
            budget = it[0]["budget_dkk"]
            extra = cost(it, it[6] + 1) - cost(it, it[6])
            if extra <= leftover and cost(it, it[6] + 1) <= budget * 1.3:
                fill = cost(it, it[6]) / budget
                if fill < best_fill:
                    best, best_fill = it, fill
        if best is None:
            break
        leftover -= cost(best, best[6] + 1) - cost(best, best[6])
        best[6] += 1

    for o, d, px, ccy, fx, eur, n in plan:
        t = o["ticker"]
        if n <= 0:
            trades.append({"date": d.strftime("%Y-%m-%d"), "strategy": label, "ticker": t, "action": "SKIPPED",
                           "shares": 0, "value": 0, "fee": 0, "price": round(px, 2), "currency": ccy,
                           "reason": "Not enough cash for one whole share at the open"})
            continue
        r = _CM.buy_receipt(px, n, ccy, fx, eur)
        fp = r["price"]
        if r["total"] > p["cash"] + 1e-6:
            continue
        p["cash"] -= r["total"]
        _book(p, r)
        pos = p["positions"].setdefault(t, {"shares": 0, "cost_dkk": 0.0, "entry_price": fp,
                                           "entry_date": d.strftime("%Y-%m-%d")})
        pos["shares"] += n
        pos["cost_dkk"] += r["total"]
        trades.append(_trade(label, d, t, "BUY", r, ccy, o["reason"]))
    p["pending"] = keep
    return trades


def _trade(label, d, t, action, r, ccy, reason):
    fee = r["commission"] + r["fx_fee"] + r["slippage"]
    return {"date": d.strftime("%Y-%m-%d"), "strategy": label, "ticker": t, "action": action,
            "shares": r["shares"], "price": round(r["price"], 4), "currency": ccy,
            "value": round(r["gross"], 2), "fee": round(fee, 2),
            "commission": round(r["commission"], 2), "fx_fee": round(r["fx_fee"], 2),
            "slippage": round(r["slippage"], 2), "reason": reason}


def year_end_tax(p: Dict[str, Any], prev_year_end_value: float, new_year: int, label: str, date: str):
    """ASK: 17% of last year's gain (mark-to-market), losses carried forward, paid from the account."""
    gain = prev_year_end_value - p["year_start_value"]
    tax, carry = ask_tax(gain, p["loss_carry"], _CM.tax_pct)
    p["loss_carry"] = carry
    p["cash"] -= tax
    p["costs"]["tax"] += tax
    p["year"] = new_year
    p["year_start_value"] = prev_year_end_value - tax
    return {"date": date, "strategy": label, "ticker": "ASK tax", "action": "TAX", "value": round(tax, 2),
            "fee": round(tax, 2), "reason": f"17% of {p['year'] - 1} gain of {gain:,.0f} kr"
            + (f"; loss carried forward {carry:,.0f} kr" if carry else "")}


def tax_cover_order(p: Dict[str, Any], mk: Market, day, as_of: str) -> Optional[Dict[str, Any]]:
    """If paying tax left cash negative, sell just enough shares of the largest holding."""
    if p["cash"] >= 0 or not p["positions"]:
        return None
    def val(t):
        return p["positions"][t]["shares"] * (mk.last_close(t, day) or 0) * mk.rate(mk.ccy.get(t, "USD"), day)
    big = max(p["positions"], key=val)
    per_share = (mk.last_close(big, day) or 1) * mk.rate(mk.ccy.get(big, "USD"), day) * (1 - _CM.fx_fee_pct - 0.01)
    n = min(p["positions"][big]["shares"], math.ceil(-p["cash"] / per_share))
    return {"ticker": big, "side": -1, "placed": as_of, "shares": n,
            "reason": f"Sell {n} share(s) to cover the ASK tax payment"}


def accrued_tax(p: Dict[str, Any], current_value: float) -> float:
    """Tax that would be due if the year ended today."""
    gain = current_value - p["year_start_value"] - p["loss_carry"]
    return max(gain, 0.0) * _CM.tax_pct
