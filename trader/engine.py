"""Signals, ranking and the two paper portfolios."""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

STRATEGIES = ("skill", "momentum")


# ── Signals ────────────────────────────────────────────────────────────────────

def price_signals(prices: pd.DataFrame, cfg: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    m = cfg["momentum"]
    look, skip, sma_n = m["lookback_days"], m["skip_recent_days"], m["trend_sma_days"]
    out = {}
    for t in prices.columns:
        s = prices[t].dropna()
        if len(s) < 2:
            continue
        px = float(s.iloc[-1])
        sig = {"price": px, "day_pct": (px / float(s.iloc[-2]) - 1) * 100}
        if len(s) > look:
            sig["mom_pct"] = (float(s.iloc[-1 - skip]) / float(s.iloc[-1 - look]) - 1) * 100
        if len(s) >= sma_n:
            sma = float(s.iloc[-sma_n:].mean())
            sig["sma200"] = sma
            sig["trend_up"] = px > sma
        if len(s) >= 51:
            sma50_now = float(s.iloc[-50:].mean())
            sma50_prev = float(s.iloc[-51:-1].mean())
            sig["above50"] = px > sma50_now
            sig["broke50"] = px < sma50_now and float(s.iloc[-2]) >= sma50_prev
        sig["spark"] = [round(float(v), 2) for v in s.iloc[-90:].tolist()]
        out[t] = sig
    return out


def _pct_rank(values: Dict[str, float]) -> Dict[str, float]:
    if not values:
        return {}
    s = pd.Series(values)
    return (s.rank(pct=True)).to_dict()


def rank_universe(rows: Dict[str, Dict[str, Any]], cfg: Dict[str, Any]) -> Dict[str, List[str]]:
    """Fill rank/score fields on rows; return ordered eligible lists per strategy."""
    sk = cfg["skill_strategy"]
    comp = {t: r["composite"] for t, r in rows.items() if r.get("composite") is not None}
    mom = {t: r["mom_pct"] for t, r in rows.items() if r.get("mom_pct") is not None}
    q_pct, m_pct = _pct_rank(comp), _pct_rank(mom)

    skill_scores, mom_scores = {}, {}
    for t, r in rows.items():
        reasons = []
        if r.get("mom_pct") is None:
            reasons.append("not enough price history")
        if r.get("trend_up") is False:
            reasons.append("below 200-day average")
        if not reasons:
            mom_scores[t] = r["mom_pct"]
        mom_reasons = list(reasons)

        if r.get("vetoed"):
            reasons.append("vetoed by red-flag gate")
        elif r.get("composite") is None:
            reasons.append("no skill score")
        elif r["composite"] < sk["min_composite"]:
            reasons.append(f"skill score below {sk['min_composite']:g}")
        if not reasons:
            skill_scores[t] = sk["quality_weight"] * q_pct.get(t, 0) + sk["momentum_weight"] * m_pct.get(t, 0)
        r["skill_score"] = round(skill_scores[t] * 100, 1) if t in skill_scores else None
        r["excluded"] = {"skill": reasons, "momentum": mom_reasons}

    order = {
        "skill": sorted(skill_scores, key=skill_scores.get, reverse=True),
        "momentum": sorted(mom_scores, key=mom_scores.get, reverse=True),
    }
    for sid, lst in order.items():
        for i, t in enumerate(lst):
            rows[t][f"{sid}_rank"] = i + 1
    return order


# ── Portfolio ──────────────────────────────────────────────────────────────────

def new_portfolio(cash: float, as_of: str) -> Dict[str, Any]:
    return {"cash": cash, "positions": {}, "started": as_of, "last_rebalance_month": None}


def portfolio_value(p: Dict[str, Any], px: Dict[str, float]) -> float:
    return p["cash"] + sum(pos["shares"] * px.get(t, pos.get("last_price", 0)) for t, pos in p["positions"].items())


def step_portfolio(p: Dict[str, Any], ranked: List[str], px: Dict[str, float], as_of: str,
                   cfg: Dict[str, Any], label: str, rows: Dict[str, Dict[str, Any]],
                   rank_key: str) -> List[Dict[str, Any]]:
    """Decide target holdings with a keep-band, then trade to equal weight if anything changed."""
    n, keep_within = cfg["holdings"], cfg["keep_while_rank_within"]
    cost = cfg["trade_cost_bps"] / 10_000
    rank = {t: i + 1 for i, t in enumerate(ranked)}

    held = list(p["positions"])
    keep, sells = [], {}
    for t in held:
        r = rank.get(t)
        if r is not None and r <= keep_within:
            keep.append(t)
        else:
            why = rows.get(t, {}).get("excluded", {}).get(rank_key) or []
            sells[t] = "; ".join(why) if why else (f"fell to rank #{r}, outside top {keep_within}" if r else "no longer ranked")
    target = list(keep)
    for t in ranked:
        if len(target) >= n:
            break
        if t not in target and t in px:
            target.append(t)

    month = as_of[:7]
    changed = set(target) != set(held)
    monthly = p.get("last_rebalance_month") != month
    if not changed and not monthly:
        return []

    trades: List[Dict[str, Any]] = []

    def trade(t, shares, price, reason):
        value = shares * price
        fee = abs(value) * cost
        p["cash"] -= value + fee
        trades.append({"date": as_of, "strategy": label, "ticker": t, "action": "BUY" if shares > 0 else "SELL",
                       "shares": round(abs(shares), 6), "price": round(price, 4), "value": round(abs(value), 2),
                       "fee": round(fee, 2), "reason": reason})

    for t, why in sells.items():
        pos = p["positions"].pop(t)
        price = px.get(t, pos.get("last_price"))
        pnl = (price / pos["entry_price"] - 1) * 100 if pos.get("entry_price") else 0
        trade(t, -pos["shares"], price, f"Exit: {why} ({pnl:+.1f}% since entry)")

    total = portfolio_value(p, px)
    if target:
        tgt_val = total * (1 - cost) / len(target)
        # sells/trims first so cash is available for buys
        for phase in ("trim", "buy"):
            for t in target:
                price = px[t]
                cur = p["positions"].get(t, {}).get("shares", 0.0)
                delta = tgt_val / price - cur
                if abs(delta * price) < max(1.0, 0.01 * tgt_val):
                    continue
                if (phase == "trim") != (delta < 0):
                    continue
                if cur == 0:
                    r = rows.get(t, {})
                    bits = [f"rank #{rank[t]}"]
                    if rank_key == "skill" and r.get("composite") is not None:
                        bits.append(f"skill score {r['composite']:.1f} ({r.get('grade')})")
                    if r.get("mom_pct") is not None:
                        bits.append(f"{r['mom_pct']:+.0f}% 12-1m momentum")
                    reason = "New entry: " + ", ".join(bits)
                    p["positions"][t] = {"shares": 0.0, "entry_price": price, "entry_date": as_of}
                else:
                    reason = "Rebalance to equal weight" + (" (monthly)" if monthly and not changed else "")
                trade(t, delta, price, reason)
                p["positions"][t]["shares"] += delta
    p["last_rebalance_month"] = month
    if abs(p["cash"]) < 0.005:
        p["cash"] = 0.0
    return trades


# ── Performance stats ──────────────────────────────────────────────────────────

def perf_stats(series: pd.Series) -> Dict[str, Optional[float]]:
    s = series.dropna()
    if len(s) == 0:
        return {}
    first, last = float(s.iloc[0]), float(s.iloc[-1])
    out: Dict[str, Optional[float]] = {
        "value": round(last, 2),
        "total_return_pct": round((last / first - 1) * 100, 2),
        "day_pct": round((last / float(s.iloc[-2]) - 1) * 100, 2) if len(s) > 1 else 0.0,
        "max_drawdown_pct": round(float((s / s.cummax() - 1).min()) * 100, 2),
        "days": int(len(s)),
    }
    rets = s.pct_change().dropna()
    if len(rets) >= 20:
        vol = float(rets.std()) * math.sqrt(252)
        out["volatility_pct"] = round(vol * 100, 1)
        out["sharpe"] = round(float(rets.mean()) * 252 / vol, 2) if vol > 0 else None
    span = (s.index[-1] - s.index[0]).days
    if span >= 90:
        out["cagr_pct"] = round(((last / first) ** (365.25 / span) - 1) * 100, 2)
    return out
