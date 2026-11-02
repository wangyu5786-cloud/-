"""Contest scoring and the team's execution / risk rules as plain functions."""
from __future__ import annotations

import csv
import math
from pathlib import Path

from .config import CONTEST, STRATEGY, ContestRules, StrategyRules


# --- contest scoring ---------------------------------------------------------

def rotation_bonus_rate(days: int, rules: ContestRules = CONTEST) -> float:
    for min_days, rate in rules.rotation_tiers:
        if days >= min_days:
            return rate
    return 0.0


def off_list_penalty(amount_opened: float, rules: ContestRules = CONTEST) -> float:
    return min(amount_opened * rules.off_list_rate, rules.off_list_cap)


def contest_score(account_value: float, rotation_days: int, off_list_amount: float = 0.0,
                  rules: ContestRules = CONTEST) -> float:
    """Account value + rotation bonus on profit − off-list penalty."""
    profit = max(account_value - rules.start_cash, 0.0)
    return account_value + profit * rotation_bonus_rate(rotation_days, rules) - off_list_penalty(off_list_amount, rules)


def load_universe(path: str | Path) -> set[str]:
    with open(path, newline="", encoding="utf-8") as f:
        return {r["ticker"] for r in csv.DictReader(f)}


# --- execution ---------------------------------------------------------------

def limit_order(ticker: str, budget: float, prev_close: float, premarket: float | None = None,
                live: float | None = None, rules: StrategyRules = STRATEGY) -> dict:
    """Limit price and share count for a buy.

    Reference = live price once the market is open, otherwise
    max(previous close, premarket). Steady names get a 1% buffer, volatile
    names 2%, so the order fills on a normal tick up without chasing a spike.
    """
    if live is not None:
        ref = live
    else:
        ref = max(prev_close, premarket or 0.0)
    buffer = rules.volatile_buffer if ticker in rules.volatile_tickers else rules.steady_buffer
    limit = round(ref * (1 + buffer), 2)
    shares = math.floor(budget / limit)
    return dict(ticker=ticker, reference=ref, buffer=buffer, limit=limit, shares=shares, cost=shares * limit)


def is_chasing(day_change: float, rules: StrategyRules = STRATEGY) -> bool:
    return day_change > rules.no_chase_day_gain


# --- risk checks ---------------------------------------------------------------

def drawdown(account_value: float, peak: float) -> float:
    return max(0.0, 1 - account_value / peak)


def risk_report(rows: list[dict], account_value: float, peak: float,
                day_changes: dict[str, float] | None = None, rules: StrategyRules = STRATEGY) -> list[str]:
    """Plain-language warnings for anything that breaks a rule."""
    out = []
    dd = drawdown(account_value, peak)
    if dd >= rules.brake_drawdown:
        out.append(f"BRAKE 2: drawdown {dd:.1%} >= {rules.brake_drawdown:.0%}; "
                   f"sell the weakest name and cut to {rules.brake_invested:.0%} invested")
    for r in rows:
        if r["weight"] > rules.max_single:
            out.append(f"{r['ticker']}: weight {r['weight']:.1%} above single-stock cap {rules.max_single:.0%}")
        if r["pnl_pct"] <= -rules.review_from_cost:
            out.append(f"{r['ticker']}: {r['pnl_pct']:.1%} vs cost, past the {rules.review_from_cost:.0%} review line")
        if day_changes and day_changes.get(r["ticker"], 0) <= -rules.review_day_drop:
            out.append(f"{r['ticker']}: fell {day_changes[r['ticker']]:.1%} today, past the {rules.review_day_drop:.0%} review line")
    chips = sum(r["weight"] for r in rows if r["ticker"] in rules.ai_chip_tickers)
    if chips > rules.max_ai_chips:
        out.append(f"AI chips {chips:.1%} above cap {rules.max_ai_chips:.0%}")
    return out
