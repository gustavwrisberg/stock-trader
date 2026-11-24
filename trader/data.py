"""Market data: daily closes and annual statements (yfinance), plus an offline demo feed."""
from __future__ import annotations

import time
from typing import Any, Dict, List

import numpy as np
import pandas as pd


def fetch_prices(tickers: List[str], period: str = "2y") -> pd.DataFrame:
    import yfinance as yf

    df = yf.download(tickers, period=period, auto_adjust=True, progress=False, threads=True)["Close"]
    if isinstance(df, pd.Series):
        df = df.to_frame(name=tickers[0])
    df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
    return df.sort_index().ffill(limit=3)


def fetch_statements(ticker: str) -> Dict[str, Any]:
    import yfinance as yf

    for attempt in range(3):
        try:
            t = yf.Ticker(ticker)
            frames = {"income": t.income_stmt, "balance": t.balance_sheet, "cashflow": t.cashflow}
            try:
                info = t.info or {}
            except Exception:
                info = {}
            keep = {k: info.get(k) for k in ("marketCap", "enterpriseValue", "sharesOutstanding", "trailingPE",
                                         "priceToBook", "enterpriseToEbitda", "currentPrice", "regularMarketPrice",
                                         "currency", "financialCurrency", "longName", "sector", "industry")}
            return {"frames": frames, "info": keep}
        except Exception as exc:  # network hiccup / rate limit
            if attempt == 2:
                raise
            print(f"  retry {ticker}: {exc}")
            time.sleep(3 * (attempt + 1))
    return {"frames": {}, "info": {}}


# ── Offline demo feed (used with --demo; lets the pipeline and site run without network) ──

def demo_prices(tickers: List[str], days: int = 520, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=days)
    out = {}
    for i, t in enumerate(tickers):
        drift = rng.normal(0.0004, 0.0005)
        vol = rng.uniform(0.010, 0.025)
        out[t] = 100 * np.exp(np.cumsum(rng.normal(drift, vol, days)))
    return pd.DataFrame(out, index=idx)


def demo_statements(ticker: str, seed: int) -> Dict[str, Any]:
    rng = np.random.default_rng(seed)
    years = pd.to_datetime([f"{y}-12-31" for y in (2025, 2024, 2023, 2022)])
    rev0 = rng.uniform(20e9, 300e9)
    g = rng.uniform(-0.02, 0.25)
    rev = np.array([rev0 / (1 + g) ** i for i in range(4)])
    opm = rng.uniform(0.05, 0.45)
    ni = rev * opm * 0.78
    cfo = ni * rng.uniform(0.4, 1.4)
    ta = rev * rng.uniform(0.8, 2.0)

    def frame(rows):
        return pd.DataFrame({k: v for k, v in rows.items()}, index=years).T

    income = frame({
        "Total Revenue": rev, "Gross Profit": rev * min(opm + rng.uniform(0.1, 0.4), 0.9),
        "Operating Income": rev * opm, "EBIT": rev * opm, "EBITDA": rev * (opm + 0.05),
        "Net Income": ni, "Pretax Income": ni / 0.78, "Tax Provision": ni / 0.78 * 0.22,
        "Interest Expense": rev * rng.uniform(0.002, 0.03), "Diluted EPS": ni / 1e9,
        "Diluted Average Shares": np.array([1e9 * (1 - 0.01 * i) for i in range(4)]),
    })
    balance = frame({
        "Total Assets": ta, "Current Assets": ta * 0.4, "Current Liabilities": ta * rng.uniform(0.2, 0.35),
        "Stockholders Equity": ta * rng.uniform(0.3, 0.6), "Total Debt": ta * rng.uniform(0.05, 0.4),
        "Cash Cash Equivalents And Short Term Investments": ta * rng.uniform(0.03, 0.2),
        "Ordinary Shares Number": np.array([1e9] * 4),
    })
    cashflow = frame({"Operating Cash Flow": cfo, "Free Cash Flow": cfo * 0.7, "Capital Expenditure": -cfo * 0.3})
    return {"frames": {"income": income, "balance": balance, "cashflow": cashflow},
            "info": {"sharesOutstanding": 1e9, "currentPrice": 100.0, "trailingPE": float(100e9 / ni[0]),
                     "enterpriseToEbitda": float(100e9 / (rev[0] * (opm + 0.05))), "priceToBook": 4.0}}
