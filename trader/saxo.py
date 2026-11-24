"""Minimal Saxo OpenAPI client (practice 'sim' or 'live').

Docs: https://www.developer.saxo/openapi/learn and the Reference Docs.
Only the endpoints this project needs. The access token comes from the environment (a GitHub secret),
never from code or files.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

import requests

BASE = {"sim": "https://gateway.saxobank.com/sim/openapi", "live": "https://gateway.saxobank.com/openapi"}


class SaxoAuthError(RuntimeError):
    """The token is missing, expired or revoked."""


class SaxoError(RuntimeError):
    pass


class Saxo:
    def __init__(self, token: str, environment: str = "sim", timeout: int = 20):
        if environment not in BASE:
            raise ValueError(f"unknown environment {environment!r}")
        if not token:
            raise SaxoAuthError("no access token")
        self.env = environment
        self.base = BASE[environment]
        self.s = requests.Session()
        self.s.headers.update({"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
        self.timeout = timeout

    def _req(self, method: str, path: str, **kw) -> Any:
        url = f"{self.base}/{path.lstrip('/')}"
        for attempt in range(4):
            r = self.s.request(method, url, timeout=self.timeout, **kw)
            if r.status_code == 401:
                raise SaxoAuthError("Saxo rejected the token (401): it has probably expired")
            if r.status_code in (429, 502, 503, 504) and attempt < 3:
                time.sleep(int(r.headers.get("Retry-After", 2 * (attempt + 1))))
                continue
            if r.status_code >= 400:
                raise SaxoError(f"{method} {path} -> {r.status_code}: {r.text[:500]}")
            return r.json() if r.content else None
        raise SaxoError(f"{method} {path}: gave up after retries")

    # ── account ───────────────────────────────────────────────────────────────
    def account(self) -> Dict[str, Any]:
        """The default account: AccountKey, Currency, AccountId."""
        client = self._req("GET", "port/v1/clients/me")
        accs = self._req("GET", "port/v1/accounts/me").get("Data", [])
        default = client.get("DefaultAccountKey")
        acc = next((a for a in accs if a.get("AccountKey") == default), accs[0] if accs else None)
        if not acc:
            raise SaxoError("no account found")
        return {"AccountKey": acc["AccountKey"], "AccountId": acc.get("AccountId"), "Currency": acc.get("Currency"),
                "ClientKey": client.get("ClientKey")}

    def balance(self) -> Dict[str, Any]:
        return self._req("GET", "port/v1/balances/me")

    def positions(self) -> List[Dict[str, Any]]:
        out = self._req("GET", "port/v1/positions/me", params={"FieldGroups": "PositionBase,PositionView,DisplayAndFormat"})
        return out.get("Data", [])

    def open_orders(self) -> List[Dict[str, Any]]:
        return self._req("GET", "port/v1/orders/me", params={"FieldGroups": "DisplayAndFormat"}).get("Data", [])

    # ── reference data and prices ────────────────────────────────────────────
    def find_stock(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Resolve a US ticker (e.g. 'BRK-B') to a Saxo instrument on a US exchange."""
        sym = ticker.replace("-", ".").upper()
        data = self._req("GET", "ref/v1/instruments", params={"Keywords": sym, "AssetTypes": "Stock"}).get("Data", [])
        us = ("xnas", "xnys", "arcx", "bats", "xase")
        for d in data:
            s = (d.get("Symbol") or "").lower()
            if s.split(":")[0] == sym.lower() and s.split(":")[-1] in us:
                return {"Uic": d["Identifier"], "Symbol": d.get("Symbol"), "Description": d.get("Description"),
                        "Currency": d.get("CurrencyCode")}
        return None

    def quote(self, uic: int, account_key: str) -> Dict[str, Any]:
        r = self._req("GET", "trade/v1/infoprices", params={"Uic": uic, "AssetType": "Stock", "AccountKey": account_key,
                                                              "FieldGroups": "Quote,PriceInfoDetails"})
        return r.get("Quote", {})

    # ── orders ────────────────────────────────────────────────────────────────
    def _order_body(self, account_key, uic, side, amount, ref):
        return {"AccountKey": account_key, "Uic": uic, "AssetType": "Stock", "BuySell": side, "Amount": amount,
                "OrderType": "Market", "OrderDuration": {"DurationType": "DayOrder"},
                "ManualOrder": False,  # placed by a program, not a person clicking
                "ExternalReference": ref}

    def precheck(self, account_key, uic, side, amount, ref) -> Dict[str, Any]:
        body = self._order_body(account_key, uic, side, amount, ref)
        return self._req("POST", "trade/v2/orders/precheck", json={**body, "FieldGroups": ["Costs"]})

    def place(self, account_key, uic, side, amount, ref) -> Dict[str, Any]:
        return self._req("POST", "trade/v2/orders", json=self._order_body(account_key, uic, side, amount, ref))
