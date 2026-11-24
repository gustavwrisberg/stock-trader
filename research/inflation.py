"""Danish inflation (consumer price index) for turning backtest kroner into real kroner.

Source: Statistics Denmark, table PRIS01 "Forbrugerprisindeks", all items (VAREGR 000000), index 2025=100.
PRIS01 replaced PRIS113 in February 2026. The scripts fetch the latest figures from the API when they run,
and fall back to the copy below (read 24 Nov 2026, up to October 2026) if the API is unreachable.
"""
from __future__ import annotations

import pandas as pd

API = "https://api.statbank.dk/v1/data/PRIS01/CSV?VAREGR=000000&ENHED=100&Tid=*"
CAPITAL_10Y = 80_000.0

_FALLBACK = """
2016M01 82.13 2016M02 82.69 2016M03 82.74 2016M04 82.86 2016M05 83.04 2016M06 83.11 2016M07 83.03 2016M08 82.77
2016M09 82.75 2016M10 82.94 2016M11 82.85 2016M12 82.89 2017M01 82.85 2017M02 83.52 2017M03 83.56 2017M04 83.78
2017M05 83.69 2017M06 83.59 2017M07 84.27 2017M08 84.02 2017M09 84.07 2017M10 84.17 2017M11 83.93 2017M12 83.65
2018M01 83.40 2018M02 84.04 2018M03 84.02 2018M04 84.45 2018M05 84.57 2018M06 84.53 2018M07 85.19 2018M08 84.83
2018M09 84.61 2018M10 84.86 2018M11 84.59 2018M12 84.30 2019M01 84.48 2019M02 84.92 2019M03 85.00 2019M04 85.22
2019M05 85.19 2019M06 84.98 2019M07 85.46 2019M08 85.18 2019M09 85.01 2019M10 85.31 2019M11 85.14 2019M12 85.00
2020M01 85.11 2020M02 85.56 2020M03 85.33 2020M04 85.26 2020M05 85.13 2020M06 85.22 2020M07 85.90 2020M08 85.61
2020M09 85.46 2020M10 85.68 2020M11 85.56 2020M12 85.39 2021M01 85.56 2021M02 86.07 2021M03 86.11 2021M04 86.46
2021M05 86.65 2021M06 86.73 2021M07 87.31 2021M08 87.11 2021M09 87.38 2021M10 88.18 2021M11 88.47 2021M12 88.04
2022M01 89.29 2022M02 90.18 2022M03 90.76 2022M04 92.24 2022M05 93.08 2022M06 93.84 2022M07 94.88 2022M08 94.89
2022M09 96.12 2022M10 97.17 2022M11 96.31 2022M12 95.71 2023M01 96.15 2023M02 97.03 2023M03 96.91 2023M04 97.13
2023M05 95.82 2023M06 96.13 2023M07 97.90 2023M08 97.20 2023M09 96.96 2023M10 97.20 2023M11 96.86 2023M12 96.42
2024M01 97.30 2024M02 97.82 2024M03 97.82 2024M04 97.85 2024M05 97.86 2024M06 97.89 2024M07 98.99 2024M08 98.56
2024M09 98.21 2024M10 98.77 2024M11 98.46 2024M12 98.21 2025M01 98.75 2025M02 99.82 2025M03 99.33 2025M04 99.39
2025M05 99.44 2025M06 99.69 2025M07 101.17 2025M08 100.52 2025M09 100.41 2025M10 100.89 2025M11 100.49 2025M12 100.10
2026M01 99.53 2026M02 100.54 2026M03 100.50 2026M04 100.74 2026M05 101.32 2026M06 101.56 2026M07 102.92 2026M08 102.58
2026M09 102.60 2026M10 103.10
"""

_cpi: pd.Series | None = None
source = "fallback copy"


def _parse(pairs):
    s = pd.Series({pd.Period(t.replace("M", "-"), "M"): float(v.replace(",", ".")) for t, v in pairs})
    return s.sort_index()


def cpi() -> pd.Series:
    """Monthly Danish CPI as a Series indexed by pandas monthly Periods."""
    global _cpi, source
    if _cpi is not None:
        return _cpi
    try:
        import requests
        txt = requests.get(API, timeout=20).text
        rows = [ln.split(";") for ln in txt.strip().splitlines()[1:]]
        s = _parse((r[1], r[3]) for r in rows if len(r) == 4 and r[3].strip() not in ("", ".."))
        if len(s) < 120:
            raise ValueError("too few rows")
        _cpi, source = s, "Statistics Denmark API"
    except Exception as exc:  # offline or API change: use the copy above
        print(f"(CPI fetch failed, using the stored copy: {exc})")
        toks = _FALLBACK.split()
        _cpi = _parse(zip(toks[::2], toks[1::2]))
    return _cpi


def _at(month: pd.Period) -> tuple[pd.Period, float]:
    s = cpi()
    s = s[s.index <= month]
    return s.index[-1], float(s.iloc[-1])


def last_10y(v: pd.Series, capital: float = CAPITAL_10Y) -> dict:
    """80,000 kr put in 10 years before the last date: value at the end, before and after inflation.

    The inflation-adjusted value is in kroner of the start month, so it compares directly with the 80,000 kr
    put in: above 80,000 means the money buys more than it did, below means it lost purchasing power.
    """
    w = v[v.index >= v.index[-1] - pd.DateOffset(years=10)]
    nominal = float(w.iloc[-1] / w.iloc[0] * capital)
    m0, c0 = _at(pd.Period(w.index[0], "M"))
    m1, c1 = _at(pd.Period(w.index[-1], "M"))
    infl = c1 / c0
    return {
        "value_of_80k_after_10y_kr": round(nominal),
        "value_of_80k_after_10y_real_kr": round(nominal / infl),
        "inflation_10y_pct": round((infl - 1) * 100, 1),
        "cpi_months": [str(m0), str(m1)],
    }
