"""Mirror the paper portfolio onto a Saxo account (practice 'sim' by default).

    python execute_saxo.py            # what the GitHub workflow runs on weekdays after the US open
    python execute_saxo.py --dry-run  # show the plan, place nothing

How it works (reconcile, don't replay):
  1. Work out what the paper model wants to hold: today's holdings, minus queued sells, plus queued buys
     sized from their budget at the last close.
  2. Read what the Saxo account actually holds, and any orders already waiting there.
  3. Trade only the difference. A missed or failed run is caught up next time, never doubled.

Safety:
  - config/saxo.json: enabled (kill switch), environment, dry_run, and hard limits per order, per run and
    in total; prices that moved more than max_price_move_pct from the model's price are not traded.
  - Every order is pre-checked by Saxo before it is placed and carries an ExternalReference, so the same
    order is never sent twice.
  - Live trading needs environment 'live' in the config AND the SAXO_ALLOW_LIVE secret set to LIVE_PHRASE.
  - The access token comes only from the SAXO_TOKEN secret. If it is missing or expired, nothing is traded
    and you get an email saying what to do.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import math
import os
import sys
import time
from pathlib import Path

from trader.saxo import Saxo, SaxoAuthError, SaxoError

ROOT = Path(__file__).resolve().parent
STATE_DIR = ROOT / "data" / "saxo"
LIVE_PHRASE = "I understand this trades real money"
FEE_BUFFER = 0.006  # leave room for commission, FX fee and spread when sizing buys


def load_json(p: Path, default):
    return json.loads(p.read_text()) if p.exists() else default


def write_json(p: Path, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=1))


def notify(subject: str, body: str):
    print(f"\n== {subject} ==\n{body}")
    if os.getenv("GMAIL_REFRESH_TOKEN"):
        try:
            from trader.gmail_oauth import send_email
            send_email(subject, body)
        except Exception as exc:  # email trouble must never block trading logic
            print(f"(email failed: {exc})")


def model_target(strategy: str):
    """Whole-share holdings the paper model wants after its queued orders, plus the prices it used."""
    ports = load_json(ROOT / "data/portfolios.json", {})
    dash = load_json(ROOT / "docs/data/dashboard.json", {})
    if strategy not in ports:
        raise SystemExit(f"strategy {strategy!r} not found in data/portfolios.json")
    p = ports[strategy]
    fx = float(dash.get("fx_usd") or 0)
    prices = {r["ticker"]: r.get("price") for r in dash.get("universe", [])}
    target = {t: int(pos["shares"]) for t, pos in p["positions"].items()}
    notes = {}
    for o in p.get("pending", []):
        t = o["ticker"]
        if o["side"] < 0:
            n = o.get("shares") or target.get(t, 0)
            target[t] = max(0, target.get(t, 0) - int(n))
            notes[t] = o["reason"]
        else:
            px = prices.get(t)
            if not px or not fx:
                continue
            target[t] = target.get(t, 0) + math.floor(o["budget_dkk"] / (px * fx * (1 + FEE_BUFFER)))
            notes[t] = o["reason"]
    return {t: n for t, n in target.items()}, prices, fx, notes, dash.get("as_of")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    cfg = load_json(ROOT / "config/saxo.json", {})
    env, strategy, lim = cfg.get("environment", "sim"), cfg.get("strategy", "skill"), cfg["limits"]
    dry = args.dry_run or cfg.get("dry_run", False) or os.getenv("SAXO_DRY_RUN") == "true"
    label = "practice account" if env == "sim" else "LIVE account"
    today = dt.date.today().isoformat()

    if not cfg.get("enabled", False):
        print("Saxo trading is switched off in config/saxo.json (enabled: false). Nothing to do.")
        return
    if env == "live" and os.getenv("SAXO_ALLOW_LIVE") != LIVE_PHRASE:
        notify("Saxo: live trading blocked", "config/saxo.json says 'live', but the SAXO_ALLOW_LIVE secret is not set to "
               f"the exact phrase \"{LIVE_PHRASE}\". Nothing was traded.")
        sys.exit(1)

    target, prices, fx, notes, as_of = model_target(strategy)
    state_path = STATE_DIR / "state.json"
    state = load_json(state_path, {"instruments": {}, "last_positions": {}, "last_run": None})

    token = os.getenv("SAXO_TOKEN", "").strip()
    wanted_change = {t: n for t, n in target.items() if n != state["last_positions"].get(t, 0)}
    if not token:
        if wanted_change:
            notify(f"Saxo {label}: action needed", "The model has trades waiting for Saxo, but no access token is set.\n"
                   "Get a new 24-hour token at https://www.developer.saxo/openapi/token and save it as the GitHub "
                   "secret SAXO_TOKEN, then run the 'Saxo practice trading' workflow.\n\n"
                   + "\n".join(f"  {t}: want {n} shares" for t, n in sorted(wanted_change.items())))
        else:
            print("No token and nothing to change.")
        return

    try:
        sx = Saxo(token, env)
        acct = sx.account()
        ak = acct["AccountKey"]

        # instruments (cached)
        inst = state["instruments"]
        for t in set(target) | set(state["last_positions"]):
            if t not in inst:
                found = sx.find_stock(t)
                if found:
                    inst[t] = found
                else:
                    print(f"! {t}: no US-listed Saxo instrument found; skipped")
        by_uic = {v["Uic"]: t for t, v in inst.items()}

        # what Saxo holds and has waiting
        held = {}
        for pos in sx.positions():
            base = pos.get("PositionBase", {})
            t = by_uic.get(base.get("Uic"))
            if t and base.get("AssetType") == "Stock":
                held[t] = held.get(t, 0) + int(round(base.get("Amount", 0)))
        waiting = {}
        for o in sx.open_orders():
            t = by_uic.get(o.get("Uic"))
            if t:
                waiting[t] = o.get("ExternalReference") or o.get("OrderId")

        # the difference, sells first
        plan = []
        for t in sorted(set(target) | set(held)):
            if t not in inst:
                continue
            delta = target.get(t, 0) - held.get(t, 0)
            if delta == 0:
                continue
            if t in waiting:
                print(f"  {t}: an order is already waiting at Saxo ({waiting[t]}); not adding another")
                continue
            plan.append({"ticker": t, "side": "Sell" if delta < 0 else "Buy", "shares": abs(delta),
                         "reason": notes.get(t, "Match the paper model")})
        plan.sort(key=lambda o: o["side"] != "Sell")

        log_rows, blocked = [], []
        total_buys = 0.0
        done_refs = set()
        log_path = STATE_DIR / "executions.csv"
        if log_path.exists():
            done_refs = {r["ref"] for r in csv.DictReader(log_path.open()) if r.get("status") in ("placed", "dry-run")}
        for o in plan[: lim["max_orders_per_run"]]:
            t = o["ticker"]
            uic = inst[t]["Uic"]
            ref = f"pt-{today}-{strategy}-{t}-{o['side'][0]}"[:50]
            if ref in done_refs:
                blocked.append(f"{t}: already sent today ({ref})")
                continue
            q = sx.quote(uic, ak)
            px = q.get("Ask") if o["side"] == "Buy" else q.get("Bid")
            px = px or q.get("Mid") or prices.get(t)
            model_px = prices.get(t)
            value_dkk = o["shares"] * px * fx
            why_not = None
            full_exit = o["side"] == "Sell" and target.get(t, 0) == 0
            if value_dkk < lim.get("min_trade_dkk", 0) and not full_exit:
                print(f"  {t}: difference of {o['shares']} share(s), ~{value_dkk:,.0f} kr, is below min_trade_dkk; left alone")
                continue
            if model_px and abs(px / model_px - 1) * 100 > lim["max_price_move_pct"]:
                why_not = f"price {px:.2f} is more than {lim['max_price_move_pct']}% from the model's {model_px:.2f}"
            elif value_dkk > lim["max_order_dkk"]:
                why_not = f"order of {value_dkk:,.0f} kr is above the {lim['max_order_dkk']:,} kr limit"
            elif o["side"] == "Buy" and total_buys + value_dkk > lim["max_total_buys_dkk"]:
                why_not = f"buys would total more than {lim['max_total_buys_dkk']:,} kr"
            row = {"date": today, "environment": env, "strategy": strategy, "ticker": t, "side": o["side"],
                   "shares": o["shares"], "quote": round(px, 4), "est_value_dkk": round(value_dkk, 2), "ref": ref,
                   "order_id": "", "status": "", "detail": o["reason"]}
            if why_not:
                row.update(status="blocked", detail=why_not)
                blocked.append(f"{t}: {why_not}")
                log_rows.append(row)
                continue
            pre = sx.precheck(ak, uic, o["side"], o["shares"], ref)
            if pre.get("ErrorInfo") or pre.get("PreCheckResult") not in (None, "Ok"):
                row.update(status="precheck failed", detail=json.dumps(pre.get("ErrorInfo") or pre)[:300])
                blocked.append(f"{t}: Saxo pre-check refused it")
                log_rows.append(row)
                continue
            if dry:
                row["status"] = "dry-run"
            else:
                res = sx.place(ak, uic, o["side"], o["shares"], ref)
                row.update(status="placed", order_id=str(res.get("OrderId", "")))
            if o["side"] == "Buy":
                total_buys += value_dkk
            log_rows.append(row)
        if len(plan) > lim["max_orders_per_run"]:
            blocked.append(f"{len(plan) - lim['max_orders_per_run']} more orders held back by max_orders_per_run")

        # record what happened and what Saxo holds now
        if log_rows:
            new = not log_path.exists()
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with log_path.open("a", newline="") as f:
                w = csv.DictWriter(f, fieldnames=list(log_rows[0]))
                if new:
                    w.writeheader()
                w.writerows(log_rows)
        if any(r["status"] == "placed" for r in log_rows):
            time.sleep(15)
            held = {}
            for pos in sx.positions():
                base = pos.get("PositionBase", {})
                t = by_uic.get(base.get("Uic"))
                if t and base.get("AssetType") == "Stock":
                    held[t] = held.get(t, 0) + int(round(base.get("Amount", 0)))
        state.update(last_positions=held, last_run=today, account_currency=acct.get("Currency"), environment=env)
        write_json(state_path, state)
        diff = {t: {"model": target.get(t, 0), "saxo": held.get(t, 0)} for t in sorted(set(target) | set(held))
                if target.get(t, 0) != held.get(t, 0)}
        write_json(STATE_DIR / "reconcile.json", {"date": today, "model_as_of": as_of, "environment": env,
                                                  "strategy": strategy, "model": target, "saxo": held,
                                                  "differences": diff, "orders": log_rows})

        if log_rows or blocked:
            lines = [f"Saxo {label}, {today}", ""]
            lines += [f"  {r['status'].upper():<15} {r['side']} {r['shares']} {r['ticker']} (~{r['est_value_dkk']:,.0f} kr) - {r['detail']}"
                      for r in log_rows]
            if blocked:
                lines += ["", "Held back:"] + [f"  {b}" for b in blocked]
            lines += ["", "Still different from the model:" if diff else "Saxo now matches the model."]
            lines += [f"  {t}: model {v['model']}, Saxo {v['saxo']}" for t, v in diff.items()]
            notify(f"Saxo {label}: {sum(r['status'] in ('placed', 'dry-run') for r in log_rows)} orders"
                   + (" (dry run)" if dry else ""), "\n".join(lines))
        else:
            print("Nothing to trade: Saxo matches the model, or the differences are too small to be worth a fee.")
    except SaxoAuthError as exc:
        notify(f"Saxo {label}: token expired", f"{exc}.\nGet a new 24-hour token at "
               "https://www.developer.saxo/openapi/token, save it as the GitHub secret SAXO_TOKEN, and rerun the "
               "'Saxo practice trading' workflow. Nothing was traded.")
    except SaxoError as exc:
        write_json(STATE_DIR / "last_error.json", {"date": today, "error": str(exc)})
        notify(f"Saxo {label}: error, nothing more was traded", str(exc))
        sys.exit(1)


if __name__ == "__main__":
    main()
