"""Daily paper-trading run.

    python run.py            # live run (needs internet; this is what GitHub Actions runs)
    python run.py --demo     # offline run on synthetic data, writes to demo/ (for testing the site)

Steps: fetch prices -> refresh fundamentals weekly -> score every company with the
stock-analysis skill -> rank -> trade both paper portfolios -> write site data -> email.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
from pathlib import Path

import pandas as pd

from trader import data as feed
from trader.engine import STRATEGIES, new_portfolio, perf_stats, portfolio_value, price_signals, rank_universe, step_portfolio
from trader.fundamentals import SOURCE, compute_metrics, valuation_metrics
from trader.scoring import SKILL_DIR, score_company

ROOT = Path(__file__).resolve().parent
LABELS = {"skill": "Skill-scored", "momentum": "Momentum only", "spy": "S&P 500 (SPY)"}


def load_json(path: Path, default):
    return json.loads(path.read_text()) if path.exists() else default


def write_json(path: Path, obj, indent=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=indent, default=lambda o: None if isinstance(o, float) and o != o else o))


def skill_version() -> str:
    try:
        return (SKILL_DIR / "VERSION").read_text().strip()
    except OSError:
        return "vendored"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true", help="offline synthetic data; writes to demo/")
    ap.add_argument("--refresh-fundamentals", action="store_true")
    ap.add_argument("--no-email", action="store_true")
    ap.add_argument("--demo-offset", type=int, default=0, help=argparse.SUPPRESS)
    args = ap.parse_args()

    universe = load_json(ROOT / "config/universe.json", {})
    cfg = load_json(ROOT / "config/strategy.json", {})
    manual_flags = load_json(ROOT / "config/flags.json", {}).get("flags", {})
    tickers = list(universe["tickers"])
    bench = universe.get("benchmark", "SPY")
    ccy = cfg.get("currency", "USD").upper()
    fx_ticker = None if ccy == "USD" else f"{ccy}=X"  # Yahoo: units of ccy per 1 USD

    state_dir = ROOT / ("demo/data" if args.demo else "data")
    site_json = ROOT / ("demo/dashboard.json" if args.demo else "docs/data/dashboard.json")
    state_dir.mkdir(parents=True, exist_ok=True)

    # ── 1. Prices ─────────────────────────────────────────────────────────────
    extra = [bench] + ([fx_ticker] if fx_ticker else [])
    print(f"Fetching prices for {len(tickers)} tickers + {', '.join(extra)}")
    prices = feed.demo_prices(tickers + extra) if args.demo else feed.fetch_prices(tickers + extra)
    if args.demo and args.demo_offset:
        prices = prices.iloc[:-args.demo_offset]
    prices = prices.dropna(how="all")
    # use the last date most of the universe has a close for
    coverage = prices.notna().sum(axis=1)
    prices = prices.loc[coverage[coverage >= 0.8 * prices.shape[1]].index]
    as_of = prices.index[-1].strftime("%Y-%m-%d")
    fx = 1.0
    if fx_ticker:
        fxs = prices.pop(fx_ticker).ffill().dropna()
        if fxs.empty:
            raise SystemExit(f"No {fx_ticker} exchange rate available; aborting so values aren't mispriced")
        fx = float(fxs.iloc[-1])
    print(f"Prices as of {as_of}; 1 USD = {fx:.4f} {ccy}")
    sig = price_signals(prices, cfg)
    px = {t: s["price"] for t, s in sig.items()}

    # ── 2. Fundamentals (weekly refresh, cached) ──────────────────────────────
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
            computed = compute_metrics(raw["frames"], raw["info"], meta["sector"])
            fcache[t] = {"fetched_at": now.isoformat(timespec="seconds"), "sector": meta["sector"], **computed}
        except Exception as exc:
            print(f"    ! failed ({exc}); keeping previous data" if entry else f"    ! failed ({exc})")
    write_json(fcache_path, fcache, indent=1)

    # ── 3. Score every company with the stock-analysis skill ─────────────────
    rows = {}
    for t in tickers:
        meta = universe["tickers"][t]
        s = sig.get(t, {})
        row = {"ticker": t, "name": meta["name"], **{k: v for k, v in s.items()}}
        f = fcache.get(t)
        if f:
            metrics = dict(f.get("metrics") or {})
            metrics.update(valuation_metrics(f.get("val_inputs") or {}, s.get("price")))
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

    # ── 4. Trade the paper portfolios ─────────────────────────────────────────
    ports = load_json(state_dir / "portfolios.json", {})
    for sid in STRATEGIES:
        ports.setdefault(sid, new_portfolio(cfg["starting_cash"] / fx, as_of))
    if "spy" not in ports:
        ports["spy"] = {"shares": cfg["starting_cash"] / fx / px[bench], "started": as_of}

    trades = []
    for sid in STRATEGIES:
        new = step_portfolio(ports[sid], order[sid], px, as_of, cfg, LABELS[sid], rows, sid)
        for t in new:  # amounts in the reporting currency; price stays in USD
            t["value"] = round(t["value"] * fx, 2)
            t["fee"] = round(t["fee"] * fx, 2)
            t["price_usd"] = t.pop("price")
        trades += new
        for t, pos in ports[sid]["positions"].items():
            pos["last_price"] = px.get(t, pos.get("last_price"))
    write_json(state_dir / "portfolios.json", ports, indent=1)

    trades_path = state_dir / "trades.csv"
    tdf = pd.read_csv(trades_path) if trades_path.exists() else pd.DataFrame()
    if trades:
        tdf = pd.concat([tdf, pd.DataFrame(trades)], ignore_index=True)
        tdf.to_csv(trades_path, index=False)

    # ── 5. Equity curve ───────────────────────────────────────────────────────
    eq_path = state_dir / "equity.csv"
    eq = pd.read_csv(eq_path, index_col="date") if eq_path.exists() else pd.DataFrame(columns=["skill", "momentum", "spy", "fx"])
    eq.loc[as_of] = [round(portfolio_value(ports["skill"], px) * fx, 2), round(portfolio_value(ports["momentum"], px) * fx, 2),
                     round(ports["spy"]["shares"] * px[bench] * fx, 2), round(fx, 5)]
    eq = eq.sort_index()
    eq.index.name = "date"
    eq.to_csv(eq_path)
    eq_dt = eq.copy()
    eq_dt.index = pd.to_datetime(eq_dt.index)

    # rank history (for the site's "how picks moved" view)
    rh_path = state_dir / "rank_history.csv"
    rh = pd.read_csv(rh_path) if rh_path.exists() else pd.DataFrame()
    today = pd.DataFrame([{"date": as_of, "ticker": t, "composite": r.get("composite"), "skill_rank": r.get("skill_rank"),
                           "momentum_rank": r.get("momentum_rank"), "mom_pct": round(r["mom_pct"], 2) if r.get("mom_pct") is not None else None}
                          for t, r in rows.items()])
    if not rh.empty:
        rh = rh[rh["date"] != as_of]
    rh = pd.concat([rh, today], ignore_index=True)
    rh.to_csv(rh_path, index=False)

    # ── 6. Alerts ─────────────────────────────────────────────────────────────
    drop = cfg["alerts"]["daily_drop_pct"]
    held = {t for sid in STRATEGIES for t in ports[sid]["positions"]}
    alerts = []
    for t in sorted(held):
        s = sig.get(t, {})
        if s.get("day_pct") is not None and s["day_pct"] <= drop:
            alerts.append(f"{t} fell {abs(s['day_pct']):.1f}% today")
        if s.get("broke50"):
            alerts.append(f"{t} closed below its 50-day average")
        if rows[t].get("vetoed"):
            alerts.append(f"{t} hit a red-flag veto in the skill's gates")

    # ── 7. Site data ──────────────────────────────────────────────────────────
    strategies = []
    for sid in STRATEGIES:
        p = ports[sid]
        total = portfolio_value(p, px)
        holdings = []
        for t, pos in sorted(p["positions"].items(), key=lambda kv: -kv[1]["shares"] * px.get(kv[0], 0)):
            price = px.get(t, pos.get("last_price"))
            r = rows.get(t, {})
            holdings.append({"ticker": t, "name": r.get("name"), "shares": round(pos["shares"], 6), "price": round(price, 2),
                             "value": round(pos["shares"] * price * fx, 2), "weight_pct": round(pos["shares"] * price / total * 100, 1),
                             "entry_price": round(pos["entry_price"], 2), "entry_date": pos["entry_date"],
                             "pnl_pct": round((price / pos["entry_price"] - 1) * 100, 2), "day_pct": round(r.get("day_pct", 0), 2),
                             "composite": r.get("composite"), "grade": r.get("grade"), "sector_label": r.get("sector_label")})
        strategies.append({"id": sid, "label": LABELS[sid], "cash": round(p["cash"] * fx, 2), "started": p["started"],
                           "stats": perf_stats(eq_dt[sid]), "holdings": holdings})

    def clean(r):
        out = {k: v for k, v in r.items() if k not in ("sma200",)}
        for k in ("price", "day_pct", "mom_pct"):
            if out.get(k) is not None:
                out[k] = round(out[k], 2)
        out["held_by"] = [sid for sid in STRATEGIES if r["ticker"] in ports[sid]["positions"]]
        return out

    recent_trades = tdf.tail(300).iloc[::-1].to_dict(orient="records") if not tdf.empty else []
    dashboard = {
        "generated_at": now.isoformat(timespec="seconds") + "Z",
        "as_of": as_of,
        "demo": args.demo,
        "data_source": SOURCE,
        "currency": ccy,
        "fx_usd": round(fx, 4),
        "skill": {"name": "stock-analysis", "repo": "https://github.com/alirezarezvani/claude-skills",
                  "path": "finance/skills/stock-analysis", "version": skill_version()},
        "config": {k: v for k, v in cfg.items() if not k.startswith("_")},
        "strategies": strategies,
        "benchmark": {"id": "spy", "label": LABELS["spy"], "stats": perf_stats(eq_dt["spy"])},
        "equity": [{"date": d, **{k: (None if pd.isna(v) else v) for k, v in r.items() if k != "fx"}} for d, r in eq.iterrows()],
        "trades": recent_trades,
        "alerts": alerts,
        "universe": sorted((clean(r) for r in rows.values()),
                           key=lambda r: (r.get("skill_rank") or 999, -(r.get("composite") or -1))),
    }
    write_json(site_json, dashboard)
    print(f"Wrote {site_json.relative_to(ROOT)} - {len(trades)} trades, {len(alerts)} alerts")

    # ── 8. Email ──────────────────────────────────────────────────────────────
    if (trades or alerts) and cfg["alerts"].get("send_email") and not args.no_email and not args.demo:
        send_summary(as_of, trades, alerts, strategies, dashboard["benchmark"], cfg, ccy)


def send_summary(as_of, trades, alerts, strategies, bench, cfg, ccy="USD"):
    if not os.getenv("GMAIL_REFRESH_TOKEN"):
        print("Email skipped: GMAIL_* secrets not set")
        return
    from trader.gmail_oauth import send_email

    lines = [f"Paper trader - {as_of}", ""]
    for s in strategies + [bench]:
        st = s["stats"]
        lines.append(f"{s['label']:<16} {st.get('value', 0):>10,.2f} {ccy}   {st.get('total_return_pct', 0):+.2f}% total   {st.get('day_pct', 0):+.2f}% today")
    if alerts:
        lines += ["", "Alerts:"] + [f"  ! {a}" for a in alerts]
    if trades:
        lines += ["", "Trades:"] + [f"  [{t['strategy']}] {t['action']} {t['ticker']} {t['value']:,.0f} {ccy} - {t['reason']}" for t in trades]
    lines += ["", f"Dashboard: {cfg['alerts'].get('site_url', '')}", "Paper money only. Not investment advice."]
    subject = f"Paper trader {as_of}: {len(trades)} trades" + (f", {len(alerts)} alerts" if alerts else "")
    try:
        send_email(subject, "\n".join(lines))
    except Exception as exc:
        print(f"Email failed: {exc}")


if __name__ == "__main__":
    main()
