"""Rebuild positions from a trade log and value them at a set of prices.

Cost basis uses the average-cost method, which is what the Investopedia
simulator shows: selling part of a position leaves the average cost of the
remaining shares unchanged and books the difference as realised P&L.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Trade:
    date: str
    ticker: str
    side: str  # "BUY" or "SELL"
    shares: int
    price: float
    note: str = ""


@dataclass
class Position:
    ticker: str
    shares: int = 0
    avg_cost: float = 0.0
    realised: float = 0.0

    @property
    def cost_basis(self) -> float:
        return self.shares * self.avg_cost


def load_trades(path: str | Path) -> list[Trade]:
    with open(path, newline="", encoding="utf-8") as f:
        return [
            Trade(
                date=r["date"],
                ticker=r["ticker"].strip().upper(),
                side=r["side"].strip().upper(),
                shares=int(r["shares"]),
                price=float(r["price"]),
                note=r.get("note", ""),
            )
            for r in csv.DictReader(f)
        ]


def load_prices(path: str | Path) -> dict[str, float]:
    with open(path, newline="", encoding="utf-8") as f:
        return {r["ticker"].strip().upper(): float(r["close"]) for r in csv.DictReader(f)}


def build_positions(trades: list[Trade]) -> dict[str, Position]:
    """Replay trades in order and return open and closed positions."""
    book: dict[str, Position] = {}
    for t in sorted(trades, key=lambda x: x.date):
        p = book.setdefault(t.ticker, Position(t.ticker))
        if t.side == "BUY":
            total = p.cost_basis + t.shares * t.price
            p.shares += t.shares
            p.avg_cost = total / p.shares
        elif t.side == "SELL":
            if t.shares > p.shares:
                raise ValueError(f"{t.date}: selling {t.shares} {t.ticker} but only {p.shares} held")
            p.realised += t.shares * (t.price - p.avg_cost)
            p.shares -= t.shares
            if p.shares == 0:
                p.avg_cost = 0.0
        else:
            raise ValueError(f"unknown side {t.side!r}")
    return book


def cash_after(trades: list[Trade], start_cash: float) -> float:
    cash = start_cash
    for t in trades:
        cash += (-1 if t.side == "BUY" else 1) * t.shares * t.price
    return cash


def rotation_days(trades: list[Trade], first_build_day: str) -> list[str]:
    """Distinct trading days with at least one trade, excluding the build day."""
    return sorted({t.date for t in trades if t.date != first_build_day})


@dataclass
class Snapshot:
    cash: float
    rows: list[dict]

    @property
    def equity(self) -> float:
        return sum(r["value"] for r in self.rows)

    @property
    def account_value(self) -> float:
        return self.cash + self.equity

    @property
    def invested(self) -> float:
        return self.equity / self.account_value


def snapshot(trades: list[Trade], prices: dict[str, float], start_cash: float) -> Snapshot:
    rows = []
    for tk, p in sorted(build_positions(trades).items()):
        if p.shares == 0:
            continue
        if tk not in prices:
            raise KeyError(f"no price for {tk}")
        px = prices[tk]
        value = p.shares * px
        rows.append(
            dict(
                ticker=tk,
                shares=p.shares,
                avg_cost=p.avg_cost,
                price=px,
                value=value,
                pnl=value - p.cost_basis,
                pnl_pct=px / p.avg_cost - 1,
                realised=p.realised,
            )
        )
    snap = Snapshot(cash=cash_after(trades, start_cash), rows=rows)
    for r in snap.rows:
        r["weight"] = r["value"] / snap.account_value
    return snap
