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
        if cfg["momentum"].get("trend_filter", True) and r.get("trend_up") is False:
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


# ── Orders ─────────────────────────────────────────────────────────────────────

def decide_orders(p: Dict[str, Any], ranked: List[str], rows: Dict[str, Dict[str, Any]], cfg: Dict[str, Any],
                  rank_key: str, total_dkk: float, est_share_cost_dkk: Dict[str, float], as_of: str,
                  new_period: bool) -> List[Dict[str, Any]]:
    """Orders for the next open. Red-flag vetoes exit any day; everything else waits for the
    rebalance day. No trims: with a minimum fee per trade, nudging weights costs more than it earns."""
    n, band = cfg["holdings"], cfg["keep_while_rank_within"]
    rank = {t: i + 1 for i, t in enumerate(ranked)}
    held = list(p["positions"])
    orders = []
    for t in held:
        r = rows.get(t, {})
        why = None
        if rank_key == "skill" and r.get("vetoed"):
            why = "Exit: red-flag veto from the skill's gates"
        elif new_period:
            ex = r.get("excluded", {}).get(rank_key) or []
            if ex:
                why = "Exit: " + "; ".join(ex)
            elif rank.get(t, 999) > band:
                why = f"Exit: fell to rank #{rank.get(t)}, outside the top {band}"
        if why:
            orders.append({"ticker": t, "side": -1, "placed": as_of, "reason": why})
    if not new_period:
        return orders
    staying = [t for t in held if t not in {o["ticker"] for o in orders}]
    budget = total_dkk / n
    slots = n - len(staying)
    for t in ranked:
        if slots <= 0:
            break
        if t in staying:
            continue
        cost1 = est_share_cost_dkk.get(t)
        if cost1 is None or cost1 > budget:
            rows[t].setdefault("notes", []).append(
                f"one share (~{cost1:,.0f} kr) costs more than a position budget ({budget:,.0f} kr)" if cost1 else "no price")
            continue
        r = rows.get(t, {})
        bits = [f"rank #{rank[t]}"]
        if rank_key == "skill" and r.get("composite") is not None:
            bits.append(f"skill score {r['composite']:.1f} ({r.get('grade')})")
        if r.get("mom_pct") is not None:
            bits.append(f"{r['mom_pct']:+.0f}% 12-1m momentum")
        orders.append({"ticker": t, "side": 1, "placed": as_of, "budget_dkk": round(budget, 2),
                       "reason": "New entry: " + ", ".join(bits)})
        slots -= 1
    return orders


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
