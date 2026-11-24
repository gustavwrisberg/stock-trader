"""Turn annual financial statements into the metric keys the stock-analysis skill scores.

The skill's rule is "never invent a number": every metric here is either computed from
a reported line item or left out. A missing metric is dropped by score.py and the
remaining categories are renormalised -- it is never scored as zero.

Source caveat (also shown on the website): statements come from Yahoo Finance via
yfinance, which the skill classes as an *aggregator* -- fine for an automated screen,
never a source of record for a real investment decision.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

SOURCE = "Yahoo Finance via yfinance (aggregator, unverified)"

# yfinance row labels vary a little between companies; first match wins.
ROWS = {
    "revenue": ["Total Revenue", "Operating Revenue"],
    "gross_profit": ["Gross Profit"],
    "operating_income": ["Operating Income", "Total Operating Income As Reported"],
    "ebit": ["EBIT"],
    "ebitda": ["EBITDA", "Normalized EBITDA"],
    "net_income": ["Net Income Common Stockholders", "Net Income"],
    "pretax": ["Pretax Income"],
    "tax": ["Tax Provision"],
    "interest": ["Interest Expense", "Interest Expense Non Operating"],
    "eps": ["Diluted EPS", "Basic EPS"],
    "shares": ["Diluted Average Shares", "Basic Average Shares"],
    "total_assets": ["Total Assets"],
    "current_assets": ["Current Assets"],
    "current_liabilities": ["Current Liabilities"],
    "equity": ["Stockholders Equity", "Common Stock Equity"],
    "total_debt": ["Total Debt"],
    "cash": ["Cash Cash Equivalents And Short Term Investments", "Cash And Cash Equivalents"],
    "receivables": ["Accounts Receivable", "Receivables"],
    "shares_out": ["Ordinary Shares Number", "Share Issued"],
    "cfo": ["Operating Cash Flow", "Cash Flow From Continuing Operating Activities"],
    "fcf": ["Free Cash Flow"],
    "capex": ["Capital Expenditure"],
}

FINANCIAL_SECTORS = {"banks", "nbfc", "insurance", "mortgage-reit-specialty-finance"}


def _series(frames: Dict[str, Any], key: str) -> List[Optional[float]]:
    """Return newest-first annual values for a logical row, across the three statements."""
    for frame in frames.values():
        if frame is None or getattr(frame, "empty", True):
            continue
        for label in ROWS[key]:
            if label in frame.index:
                vals = []
                for v in frame.loc[label].tolist():
                    try:
                        f = float(v)
                        vals.append(None if math.isnan(f) else f)
                    except (TypeError, ValueError):
                        vals.append(None)
                return vals
    return []


def _at(s: List[Optional[float]], i: int = 0) -> Optional[float]:
    return s[i] if len(s) > i else None


def _div(a, b) -> Optional[float]:
    if a is None or b is None or b == 0:
        return None
    return a / b


def _avg(a, b) -> Optional[float]:
    if a is None:
        return b
    if b is None:
        return a
    return (a + b) / 2


def _cagr(s: List[Optional[float]]) -> Optional[tuple]:
    """CAGR from the oldest to the newest available positive value. Returns (pct, years)."""
    pts = [(i, v) for i, v in enumerate(s) if v is not None]
    if len(pts) < 3:
        return None
    (i0, new), (i1, old) = pts[0], pts[-1]
    years = i1 - i0
    if years < 2 or new <= 0 or old <= 0:
        return None
    return ((new / old) ** (1 / years) - 1) * 100, years


def _m(value: Optional[float], period: str, note: Optional[str] = None, digits: int = 2):
    if value is None or isinstance(value, complex) or math.isnan(value) or math.isinf(value):
        return None
    out = {"value": round(value, digits), "source": SOURCE, "period": period}
    if note:
        out["note"] = note
    return out


def compute_metrics(frames: Dict[str, Any], info: Dict[str, Any], sector: str) -> Dict[str, Any]:
    """Statement-based metrics in score.py's input shape, plus inputs for daily revaluation."""
    g = {k: _series(frames, k) for k in ROWS}

    period = "latest FY"
    inc = frames.get("income")
    if inc is not None and not getattr(inc, "empty", True):
        try:
            period = f"FY{inc.columns[0].year}"
        except Exception:
            pass

    rev, ni, eq, ta = (_at(g["revenue"]), _at(g["net_income"]), _at(g["equity"]), _at(g["total_assets"]))
    ebit = _at(g["ebit"]) or _at(g["operating_income"])
    ebitda = _at(g["ebitda"])
    debt, cash = _at(g["total_debt"]) or 0.0, _at(g["cash"]) or 0.0
    cfo, fcf = _at(g["cfo"]), _at(g["fcf"])
    if fcf is None and cfo is not None and _at(g["capex"]) is not None:
        fcf = cfo + _at(g["capex"])  # capex is reported negative

    shares_now = info.get("sharesOutstanding") or _at(g["shares_out"])

    avg_eq = _avg(eq, _at(g["equity"], 1))
    avg_ta = _avg(ta, _at(g["total_assets"], 1))

    metrics: Dict[str, Any] = {}

    def put(key, value, note=None, digits=2):
        m = _m(value, period, note, digits)
        if m is not None:
            metrics[key] = m

    # ── Shared: returns on equity, dilution, P/E ─────────────────────────────
    if avg_eq and avg_eq > 0:
        put("roe_pct", _div(ni, avg_eq) * 100 if ni is not None else None)
    sh = [v for v in g["shares"] if v] or [v for v in g["shares_out"] if v]
    if len(sh) >= 3:
        put("dilution_5y_pct", (sh[0] / sh[-1] - 1) * 100, f"{len(sh) - 1}-year share-count change (5y proxy)")
    # Valuation inputs. Price is USD but ADRs (TSM, NVO, TM, ASML...) report in local currency, so
    # multiples are anchored on Yahoo's currency-adjusted figures at fetch time and then scaled
    # by the price move since. Ratios between two statement lines (FCF/NI) are currency-neutral.
    same_ccy = (info.get("financialCurrency") or "USD") == (info.get("currency") or "USD")
    px0 = info.get("currentPrice") or info.get("regularMarketPrice")
    pe0 = info.get("trailingPE")
    if pe0 is None and same_ccy and px0 and shares_now and ni and ni > 0:
        pe0 = px0 * shares_now / ni
    pb0 = info.get("priceToBook")
    if pb0 is None and same_ccy and px0 and shares_now and eq and eq > 0:
        pb0 = px0 * shares_now / eq
    mcap0, ev0 = info.get("marketCap"), info.get("enterpriseValue")
    val_inputs = {"price0": px0, "pe0": pe0, "pb0": pb0, "ev_ebitda0": info.get("enterpriseToEbitda"),
                  "mcap_to_ev": (mcap0 / ev0) if mcap0 and ev0 and ev0 > 0 else None,
                  "fcf_to_ni": (fcf / ni) if fcf is not None and ni and ni > 0 else None,
                  "period": period, "sector": sector}

    if sector in FINANCIAL_SECTORS:
        # Banks/insurers: EV, EBITDA and ROCE are undefined -- the skill uses its own set.
        if avg_ta and ni is not None:
            put("roa_pct", ni / avg_ta * 100)
        c = _cagr(g["equity"])
        if c:
            put("book_value_cagr_5y_pct", c[0], f"{c[1]}-year CAGR (5y proxy)")
        return {"metrics": metrics, "flags": {}, "period": period, "val_inputs": val_inputs}

    # ── Profitability ─────────────────────────────────────────────────────────
    cur_liab = _at(g["current_liabilities"])
    if ebit is not None and ta and cur_liab is not None and ta - cur_liab > 0:
        put("roce_pct", ebit / (ta - cur_liab) * 100, "EBIT / (total assets - current liabilities)")
    if rev:
        put("opm_pct", _div(_at(g["operating_income"]) or ebit, rev) * 100 if (_at(g["operating_income"]) or ebit) is not None else None)
        if _at(g["gross_profit"]) is not None:
            put("gross_margin_pct", _at(g["gross_profit"]) / rev * 100)

    # ── Earnings quality ──────────────────────────────────────────────────────
    cfo3 = [v for v in g["cfo"][:3] if v is not None]
    ni3 = [v for v in g["net_income"][:3] if v is not None]
    flags: Dict[str, Any] = {}
    if len(cfo3) == 3 and len(ni3) == 3 and sum(ni3) > 0:
        ratio = sum(cfo3) / sum(ni3)
        put("cfo_to_pat_3y", ratio)
        if ratio < 0.5:
            flags["cashflow_profit_divergence"] = {
                "present": True,
                "evidence": f"3y cumulative operating cash flow is {ratio:.0%} of net income ({SOURCE})",
            }
    if rev and fcf is not None:
        put("fcf_margin_pct", fcf / rev * 100)
    if ni is not None and cfo is not None and avg_ta:
        put("accruals_ratio_pct", (ni - cfo) / avg_ta * 100)
    pretax, tax = _at(g["pretax"]), _at(g["tax"])
    if pretax and pretax > 0 and tax is not None:
        put("effective_tax_rate_pct", tax / pretax * 100)

    # ── Balance sheet ─────────────────────────────────────────────────────────
    if ebitda and ebitda > 0:
        put("net_debt_to_ebitda", (debt - cash) / ebitda)
    interest = _at(g["interest"])
    if ebit is not None and interest and abs(interest) > 0:
        put("interest_coverage_x", min(ebit / abs(interest), 999))
    put("current_ratio", _div(_at(g["current_assets"]), cur_liab))

    # ── Growth ────────────────────────────────────────────────────────────────
    c = _cagr(g["revenue"])
    if c:
        put("revenue_cagr_5y_pct", c[0], f"{c[1]}-year CAGR (5y proxy)")
    c = _cagr(g["eps"])
    if c:
        put("eps_cagr_5y_pct", c[0], f"{c[1]}-year CAGR (5y proxy)")

    return {"metrics": metrics, "flags": flags, "period": period, "val_inputs": val_inputs}


def valuation_metrics(v: Dict[str, Any], price: Optional[float]) -> Dict[str, Any]:
    """Price-dependent metrics, recomputed every run from cached fetch-time multiples."""
    out: Dict[str, Any] = {}
    if not v or not price or not v.get("price0"):
        return out
    r = price / v["price0"]
    period = v.get("period", "latest FY")

    def put(key, value, note):
        m = _m(value, period, note + "; rescaled to this run's price")
        if m is not None:
            out[key] = m

    pe0 = v.get("pe0")
    if pe0 and pe0 > 0:
        put("pe_x", pe0 * r, "trailing P/E")
    if v.get("sector") in FINANCIAL_SECTORS:
        if v.get("pb0") and v["pb0"] > 0:
            put("pb_x", v["pb0"] * r, "price / book")
        return out
    if pe0 and pe0 > 0 and v.get("fcf_to_ni") is not None:
        put("fcf_yield_pct", v["fcf_to_ni"] / (pe0 * r) * 100, "FCF / market cap, via (FCF/NI) / P/E")
    e0 = v.get("ev_ebitda0")
    if e0 and e0 > 0:
        k = v.get("mcap_to_ev") or 1.0
        put("ev_ebitda_x", e0 * (1 + k * (r - 1)), "EV / EBITDA")
    return out
