"""Daily paper-trading run, modelled on a real Saxo aktiesparekonto.

    python run.py            # live run (what GitHub Actions runs every weekday after the US close)
    python run.py --demo     # offline run on synthetic data, writes to demo/

Each run: fetch prices -> book splits and dividends -> fill yesterday's orders at today's open ->
pay ASK tax at the turn of the year -> refresh fundamentals weekly -> score every company with the
stock-analysis skill -> rank -> queue orders for the next open -> write site data -> email.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
from pathlib import Path

import pandas as pd

from trader import data as feed
from trader import portfolio as pf
from trader.costs import CostModel
from trader.engine import decide_orders, perf_stats, price_signals, rank_universe
from trader.fundamentals import SOURCE, compute_metrics, valuation_metrics
from trader.scoring import SKILL_DIR, score_company

ROOT = Path(__file__).resolve().parent
SCHEMA = 2
STRATS = ("skill", "momentum", "index")
LABELS = {"skill": "Skill-scored", "momentum": "Momentum only", "index": "S&P 500 index fund"}


def load_json(path: Path, default):
    return json.loads(path.read_text()) if path.exists() else default


def _clean(o):
    """JSON has no NaN/Infinity: turn them into null (pandas uses NaN for missing numbers)."""
    if isinstance(o, float):
        return None if o != o or o in (float("inf"), float("-inf")) else o
    if isinstance(o, dict):
        return {k: _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if hasattr(o, "item"):  # numpy scalars
        return _clean(o.item())
    return o


def write_json(path: Path, obj, indent=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_clean(obj), indent=indent, allow_nan=False))


def skill_version() -> str:
    try:
        return (SKILL_DIR / "VERSION").read_text().strip()
    except OSError:
        return "vendored"


def period_key(day: pd.Timestamp, rebalance: str) -> str:
    return f"{day.year}-Q{(day.month - 1) // 3 + 1}" if rebalance == "quarterly" else f"{day.year}-{day.month:02d}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true", help="offline synthetic data; writes to demo/")
    ap.add_argument("--refresh-fundamentals", action="store_true")
    ap.add_argument("--no-email", action="store_true")
    ap.add_argument("--demo-offset", type=int, default=0, help=argparse.SUPPRESS)
    args = ap.parse_args()

    universe = load_json(ROOT / "config/universe.json", {})
    cfg = load_json(ROOT / "config/strategy.json", {})
    broker = load_json(ROOT / "config/broker.json", {})
    manual_flags = load_json(ROOT / "config/flags.json", {}).get("flags", {})
    tickers = list(universe["tickers"])
    etf = broker["etf"]["ticker"]
    cm = CostModel.from_config(broker)
    pf.set_cost_model(cm)

    state_dir = ROOT / ("demo/data" if args.demo else "data")
    site_json = ROOT / ("demo/dashboard.json" if args.demo else "docs/data/dashboard.json")
    state_dir.mkdir(parents=True, exist_ok=True)

    # ── 1. Market data ────────────────────────────────────────────────────────
    want = tickers + [etf, "SPY", "DKK=X", "EURDKK=X"]
    print(f"Fetching {len(want)} series")
    mkt = feed.demo_market(want) if args.demo else feed.fetch_market(want)
    if args.demo and args.demo_offset:
        mkt = {k: v.iloc[:-args.demo_offset] for k, v in mkt.items()}
    close_all = mkt["Close"]
    cov = close_all[tickers].notna().sum(axis=1)
    as_of_ts = cov[cov >= 0.8 * len(tickers)].index[-1]
    as_of = as_of_ts.strftime("%Y-%m-%d")
    trim = {k: v[v.index <= as_of_ts] for k, v in mkt.items()}
    fx_usd = trim["Close"]["DKK=X"].ffill()
    fx_eur = trim["Close"]["EURDKK=X"].ffill() if trim["Close"]["EURDKK=X"].notna().any() \
        else pd.Series(7.46, index=fx_usd.index)  # DKK is pegged to EUR
    if fx_usd.dropna().empty:
        raise SystemExit("No USD/DKK rate available; aborting so nothing is mispriced")
    index_ticker, index_ccy = etf, broker["etf"]["currency"]
    if trim["Close"][etf].dropna().empty:
        print(f"! {etf} has no prices; using SPY as the index-fund proxy")
        index_ticker, index_ccy = "SPY", "USD"
    ccy = {t: "USD" for t in tickers + ["SPY"]}
    ccy[etf] = broker["etf"]["currency"]
    mk = pf.Market(trim["Open"], trim["Close"], trim["Dividends"], trim["Stock Splits"], fx_usd, fx_eur, ccy)
    fx_today = mk.rate("USD", as_of_ts)
    print(f"Prices as of {as_of}; 1 USD = {fx_today:.4f} DKK")

    sig = price_signals(trim["Adj Close"][tickers], cfg)
    raw_px = {t: mk.last_close(t, as_of_ts) for t in tickers}

    # ── 2. Fundamentals (weekly, cached) and the skill's scores ──────────────
    fcache_path = state_dir / "fundamentals.json"
    fcache = load_json(fcache_path, {})
    max_age = dt.timedelta(days=cfg.get("fundamentals_refresh_days", 7))
    now = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
    for i, t in enumerate(tickers):
        meta = universe["tickers"][t]
        entry = fcache.get(t)
        fresh = entry and now - dt.datetime.fromisoformat(entry["fetched_at"]) < max_age and entry.get("sector") == meta["sector"]
        if fresh and not args.refresh_fundamentals:
            continue
        print(f"  fundamentals {t}")
        try:
            raw = feed.demo_statements(t, seed=i) if args.demo else feed.fetch_statements(t)
            fcache[t] = {"fetched_at": now.isoformat(timespec="seconds"), "sector": meta["sector"],
                         **compute_metrics(raw["frames"], raw["info"], meta["sector"])}
        except Exception as exc:
            print(f"    ! failed ({exc})")
    write_json(fcache_path, fcache, indent=1)

    rows = {}
    for t in tickers:
        meta = universe["tickers"][t]
        row = {"ticker": t, "name": meta["name"], **sig.get(t, {})}
        row["price"] = raw_px.get(t)
        f = fcache.get(t)
        if f:
            metrics = dict(f.get("metrics") or {})
            metrics.update(valuation_metrics(f.get("val_inputs") or {}, raw_px.get(t)))
            sc = score_company(t, meta["name"], meta["sector"], as_of,
                               {"metrics": metrics, "flags": f.get("flags"), "period": f.get("period")},
                               manual_flags.get(t, {}), cfg["skill_strategy"].get("weight_preset", "default"))
            if "error" in sc:
                print(f"  ! score.py failed for {t}: {sc['error']}")
            else:
                row.update(sc)
                row["fundamentals_fetched"] = f["fetched_at"][:10]
        rows[t] = row
    order = rank_universe(rows, cfg)

    # ── 3. Portfolios ─────────────────────────────────────────────────────────
    ports_path = state_dir / "portfolios.json"
    ports = load_json(ports_path, {})
    if ports and ports.get("schema") != SCHEMA:
        arch = state_dir / "archive" / f"{as_of}-v1"
        arch.mkdir(parents=True, exist_ok=True)
        for name in ("portfolios.json", "equity.csv", "trades.csv", "rank_history.csv"):
            if (state_dir / name).exists():
                shutil.move(str(state_dir / name), str(arch / name))
        print(f"Archived the previous model's state to {arch.relative_to(ROOT)}")
        ports = {}
    ports["schema"] = SCHEMA
    start_cash = float(cfg["starting_cash"])
    for sid in STRATS:
        ports.setdefault(sid, pf.new_portfolio(start_cash, as_of))

    eq_path = state_dir / "equity.csv"
    eq = pd.read_csv(eq_path, index_col="date") if eq_path.exists() else pd.DataFrame(columns=list(STRATS) + ["fx"])

    est_cost = {}
    for t in tickers:
        px = raw_px.get(t)
        if px:
            est_cost[t] = px * fx_today * (1 + cm.fx_fee_pct + cm.slippage_pct) + cm.commission_min_usd * fx_today

    events = []
    for sid in STRATS:
        p, label = ports[sid], LABELS[sid]
        if p["last_run"] == as_of:
            continue  # re-run on the same day: nothing new can have happened
        since = pd.Timestamp(p["last_run"]) if p["last_run"] else as_of_ts
        for e in pf.apply_corporate_actions(p, mk, since, as_of_ts):
            events.append({"strategy": label, **e})
        events += pf.fill_pending(p, mk, label)
        if as_of_ts.year > p["year"]:
            prev = eq[eq.index < f"{as_of_ts.year}-01-01"]
            if len(prev) and sid in prev:
                events.append(pf.year_end_tax(p, float(prev[sid].iloc[-1]), as_of_ts.year, label, as_of))
            else:
                p["year"], p["year_start_value"] = as_of_ts.year, pf.value(p, mk, as_of_ts)
        cover = pf.tax_cover_order(p, mk, as_of_ts, as_of)
        if cover:
            p["pending"].append(cover)
        total = pf.value(p, mk, as_of_ts)
        if sid == "index":
            if not p["positions"] and not p["pending"]:
                p["pending"] = [{"ticker": index_ticker, "side": 1, "placed": as_of, "budget_dkk": p["cash"],
                                 "reason": "Buy and hold: the index fund a Danish investor can actually buy"}]
        else:
            pk = period_key(as_of_ts, cfg.get("rebalance", "monthly"))
            new_period = p["last_period"] != pk
            pending_t = {o["ticker"] for o in p["pending"]}
            orders = []
            for o in decide_orders(p, order[sid], rows, cfg, sid, total, est_cost, as_of, new_period):
                if o["ticker"] in pending_t and o["side"] < 0:  # a full exit replaces a partial tax-cover sale
                    p["pending"] = [x for x in p["pending"] if x["ticker"] != o["ticker"]]
                elif o["ticker"] in pending_t:
                    continue
                orders.append(o)
            p["pending"] += orders
            if new_period:
                p["last_period"] = pk
        p["last_run"] = as_of
    write_json(ports_path, ports, indent=1)

    trades_path = state_dir / "trades.csv"
    tdf = pd.read_csv(trades_path) if trades_path.exists() else pd.DataFrame()
    if events:
        tdf = pd.concat([tdf, pd.DataFrame(events)], ignore_index=True)
        tdf.to_csv(trades_path, index=False)

    vals = {sid: pf.value(ports[sid], mk, as_of_ts) for sid in STRATS}
    eq.loc[as_of] = [round(vals[s], 2) for s in STRATS] + [round(fx_today, 5)]
    eq = eq.sort_index()
    eq.index.name = "date"
    eq.to_csv(eq_path)
    eq_dt = eq.copy()
    eq_dt.index = pd.to_datetime(eq_dt.index)

    # ── 4. Alerts ─────────────────────────────────────────────────────────────
    drop = cfg["alerts"]["daily_drop_pct"]
    held = {t for sid in ("skill", "momentum") for t in ports[sid]["positions"]}
    alerts = []
    for t in sorted(held):
        s = sig.get(t, {})
        if s.get("day_pct") is not None and s["day_pct"] <= drop:
            alerts.append(f"{t} fell {abs(s['day_pct']):.1f}% today")
        if rows[t].get("vetoed"):
            alerts.append(f"{t} hit a red-flag veto in the skill's gates; it will be sold at the next open")

    # ── 5. Site data ──────────────────────────────────────────────────────────
    def holding_rows(p, total):
        out = []
        for t, pos in p["positions"].items():
            c = mk.ccy.get(t, "USD")
            px = mk.last_close(t, as_of_ts) or pos.get("entry_price")
            v = pos["shares"] * px * mk.rate(c, as_of_ts)
            r = rows.get(t, {})
            out.append({"ticker": t, "name": r.get("name") or broker["etf"]["name"] if t == etf else r.get("name", t),
                        "shares": pos["shares"], "price": round(px, 2), "currency": c, "value": round(v, 2),
                        "weight_pct": round(v / total * 100, 1) if total else 0, "entry_price": round(pos["entry_price"], 2),
                        "entry_date": pos["entry_date"], "cost_dkk": round(pos["cost_dkk"], 2),
                        "pnl_pct": round((v / pos["cost_dkk"] - 1) * 100, 2) if pos["cost_dkk"] else 0,
                        "day_pct": round(r.get("day_pct", 0) or 0, 2), "composite": r.get("composite"), "grade": r.get("grade")})
        return sorted(out, key=lambda h: -h["value"])

    strategies = []
    for sid in STRATS:
        p, total = ports[sid], vals[sid]
        accrued = pf.accrued_tax(p, total)
        costs = {k: round(v, 2) for k, v in p["costs"].items()}
        strategies.append({
            "id": sid, "label": LABELS[sid], "cash": round(p["cash"], 2), "started": p["started"],
            "stats": perf_stats(eq_dt[sid]), "holdings": holding_rows(p, total),
            "pending": [{**o, "name": rows.get(o["ticker"], {}).get("name") or broker["etf"]["name"]} for o in p["pending"]],
            "costs": costs, "costs_total": round(sum(costs.values()) - costs["tax"], 2), "tax_paid": costs["tax"],
            "dividends_net": round(p["dividends_net"], 2), "tax_accrued": round(accrued, 2),
            "after_tax_value": round(total - accrued, 2), "next_rebalance": None if sid == "index" else cfg.get("rebalance", "monthly"),
        })

    def clean(r):
        out = {k: v for k, v in r.items() if k not in ("sma200",)}
        for k in ("price", "day_pct", "mom_pct"):
            if out.get(k) is not None:
                out[k] = round(out[k], 2)
        out["held_by"] = [s for s in ("skill", "momentum") if r["ticker"] in ports[s]["positions"]]
        out["share_cost_dkk"] = round(est_cost[r["ticker"]]) if r["ticker"] in est_cost else None
        return out

    research = load_json(ROOT / "research/decision.json", None)
    recent = tdf.tail(400).iloc[::-1].to_dict(orient="records") if not tdf.empty else []
    dashboard = {
        "generated_at": now.isoformat(timespec="seconds") + "Z",
        "as_of": as_of, "demo": args.demo, "data_source": SOURCE,
        "currency": "DKK", "fx_usd": round(fx_today, 4),
        "broker": {k: v for k, v in broker.items() if not k.startswith("_") and k != "alternatives"},
        "skill": {"name": "stock-analysis", "repo": "https://github.com/alirezarezvani/claude-skills",
                  "path": "finance/skills/stock-analysis", "version": skill_version()},
        "config": {k: v for k, v in cfg.items() if not k.startswith("_")},
        "strategies": strategies,
        "equity": [{"date": d, **{k: (None if pd.isna(v) else v) for k, v in r.items() if k != "fx"}} for d, r in eq.iterrows()],
        "trades": recent, "alerts": alerts,
        "research": research,
        "universe": sorted((clean(r) for r in rows.values()),
                           key=lambda r: (r.get("skill_rank") or 999, -(r.get("composite") or -1))),
    }
    write_json(site_json, dashboard)
    print(f"Wrote {site_json.relative_to(ROOT)}: {len(events)} events, {len(alerts)} alerts")
    for s in strategies:
        print(f"  {s['label']:<20} {s['stats'].get('value', 0):>10,.2f} kr  pending {[o['ticker'] for o in s['pending']]}")

    if (events or alerts) and cfg["alerts"].get("send_email") and not args.no_email and not args.demo:
        send_summary(as_of, events, alerts, strategies, cfg)


def send_summary(as_of, events, alerts, strategies, cfg):
    if not os.getenv("GMAIL_REFRESH_TOKEN"):
        print("Email skipped: GMAIL_* secrets not set")
        return
    from trader.gmail_oauth import send_email

    lines = [f"Paper trader - {as_of}", ""]
    for s in strategies:
        st = s["stats"]
        lines.append(f"{s['label']:<20} {st.get('value', 0):>10,.2f} kr   {st.get('total_return_pct', 0):+.2f}% total   {st.get('day_pct', 0):+.2f}% today")
    if alerts:
        lines += ["", "Alerts:"] + [f"  ! {a}" for a in alerts]
    if events:
        lines += ["", "Activity:"] + [f"  [{e['strategy']}] {e['action']} {e['ticker']} {e.get('value', 0) or 0:,.0f} kr - {e['reason']}" for e in events]
    pend = [(s["label"], o) for s in strategies for o in s["pending"]]
    if pend:
        lines += ["", "Orders for the next open:"] + [f"  [{lab}] {'BUY' if o['side'] > 0 else 'SELL'} {o['ticker']} - {o['reason']}" for lab, o in pend]
    lines += ["", f"Dashboard: {cfg['alerts'].get('site_url', '')}", "Paper money only. Not investment advice."]
    try:
        send_email(f"Paper trader {as_of}: {len(events)} events" + (f", {len(alerts)} alerts" if alerts else ""), "\n".join(lines))
    except Exception as exc:
        print(f"Email failed: {exc}")


if __name__ == "__main__":
    main()
