"""What a trade really costs a Danish investor (see config/broker.json).

All amounts returned in DKK. A buy of a US stock paid from a DKK account costs:
  commission  max(pct x value, min $) charged in USD and converted
  FX fee      the broker's spread on converting DKK -> USD (and back on a sale)
  slippage    paying a little above/below the quoted open on a market order
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class CostModel:
    commission_pct: float
    commission_min_usd: float
    etf_commission_pct: float
    etf_commission_min_eur: float
    fx_fee_pct: float
    slippage_pct: float
    whole_shares: bool
    withholding_pct: float
    tax_pct: float
    commission_min_dkk: float = 0.0  # banks that set the minimum in kroner (e.g. Lån & Spar: 29 kr)

    @classmethod
    def from_config(cls, b: Dict[str, Any]) -> "CostModel":
        return cls(
            commission_pct=b["stock_commission_pct"] / 100,
            commission_min_usd=b.get("stock_commission_min_usd", 0.0),
            etf_commission_pct=b["etf_commission_pct"] / 100,
            etf_commission_min_eur=b["etf_commission_min_eur"],
            fx_fee_pct=b["fx_fee_pct"] / 100,
            slippage_pct=b["slippage_pct"] / 100,
            whole_shares=b.get("whole_shares_only", True),
            withholding_pct=b["us_dividend_withholding_pct"] / 100,
            tax_pct=b["ask_tax_pct"] / 100,
            commission_min_dkk=b.get("stock_commission_min_dkk", 0.0),
        )

    def commission_local(self, value_local: float, ccy: str, fx_dkk: float, eur_dkk: float) -> float:
        """Commission in DKK. US stocks: % with a USD minimum. EUR ETFs: % with a EUR minimum."""
        if ccy == "USD":
            return max(self.commission_pct * value_local * fx_dkk, self.commission_min_usd * fx_dkk, self.commission_min_dkk)
        return max(self.etf_commission_pct * value_local, self.etf_commission_min_eur) * eur_dkk

    def fill_price(self, price: float, side: int) -> float:
        """side +1 buy, -1 sell: market orders fill slightly worse than the quote."""
        return price * (1 + side * self.slippage_pct)

    def buy_receipt(self, price: float, shares: float, ccy: str, fx_ccy_dkk: float, eur_dkk: float) -> Dict[str, float]:
        """Exact cost in DKK of buying `shares` at a quoted price, everything included."""
        px = self.fill_price(price, +1)
        gross = shares * px * fx_ccy_dkk
        fx_fee = gross * self.fx_fee_pct
        comm = self.commission_local(shares * px, ccy, fx_ccy_dkk, eur_dkk) * (1 + self.fx_fee_pct)
        return {"shares": shares, "price": px, "gross": gross, "fx_fee": fx_fee, "commission": comm,
                "slippage": shares * (px - price) * fx_ccy_dkk, "total": gross + fx_fee + comm}

    def buy(self, price: float, cash_dkk: float, budget_dkk: float, ccy: str, fx_ccy_dkk: float,
            eur_dkk: float) -> Dict[str, float]:
        """Largest whole-share buy within min(budget, cash), all costs included. Returns {} if none."""
        px = self.fill_price(price, +1)
        spend_cap = min(budget_dkk, cash_dkk)
        # cost per share in DKK incl. FX fee; commission handled after sizing
        per_share = px * fx_ccy_dkk * (1 + self.fx_fee_pct)
        shares = spend_cap / per_share
        shares = math.floor(shares) if self.whole_shares else shares
        while shares > 0:
            gross = shares * px * fx_ccy_dkk
            fx_fee = gross * self.fx_fee_pct
            comm = self.commission_local(shares * px, ccy, fx_ccy_dkk, eur_dkk) * (1 + self.fx_fee_pct)
            total = gross + fx_fee + comm
            if total <= spend_cap + 1e-9:
                return {"shares": shares, "price": px, "gross": gross, "fx_fee": fx_fee, "commission": comm,
                        "slippage": shares * (px - price) * fx_ccy_dkk, "total": total}
            shares = shares - 1 if self.whole_shares else shares * (spend_cap / total) * 0.999
        return {}

    def sell(self, price: float, shares: float, ccy: str, fx_ccy_dkk: float, eur_dkk: float) -> Dict[str, float]:
        px = self.fill_price(price, -1)
        gross = shares * px * fx_ccy_dkk
        fx_fee = gross * self.fx_fee_pct
        comm = self.commission_local(shares * px, ccy, fx_ccy_dkk, eur_dkk) * (1 + self.fx_fee_pct)
        return {"shares": shares, "price": px, "gross": gross, "fx_fee": fx_fee, "commission": comm,
                "slippage": shares * (price - px) * fx_ccy_dkk, "total": gross - fx_fee - comm}

    def dividend(self, amount_ccy: float, fx_ccy_dkk: float) -> Dict[str, float]:
        gross = amount_ccy * fx_ccy_dkk
        wht = gross * self.withholding_pct
        fx_fee = (gross - wht) * self.fx_fee_pct
        return {"gross": gross, "withholding": wht, "fx_fee": fx_fee, "net": gross - wht - fx_fee}


def ask_tax(year_gain: float, loss_carry: float, rate: float) -> tuple:
    """Aktiesparekonto: 17% of the year's gain (mark-to-market). Losses carry forward.
    Returns (tax, new_loss_carry)."""
    taxable = year_gain - loss_carry
    if taxable <= 0:
        return 0.0, -taxable
    return taxable * rate, 0.0
