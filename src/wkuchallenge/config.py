"""Contest rules and the team's own trading rules, kept in one place.

Every number used elsewhere in the package comes from here, so a rule change
is a one-line edit rather than a hunt through the code.
"""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ContestRules:
    """Rules set by the WKU Campus Investment Challenge rulebook (fall 2026)."""

    start_cash: float = 100_000.0
    start_date: str = "2026-10-26"
    end_date: str = "2026-11-20"
    # Rotation bonus: share of *profit* added to the score, by number of
    # rotation days (at most one per US trading day; the first build day
    # does not count).
    rotation_tiers: tuple = ((5, 0.05), (3, 0.03), (1, 0.02))
    # Buying a ticker outside the 100-name list costs 5% of the amount
    # opened, capped at $10k in total.
    off_list_rate: float = 0.05
    off_list_cap: float = 10_000.0


@dataclass(frozen=True)
class StrategyRules:
    """The team's own risk and execution rules (the "aggressive" plan)."""

    target_invested: float = 0.89          # share of account in stocks
    max_single: float = 0.16               # any one stock
    max_ai_chips: float = 0.28             # NVDA + TSM combined
    ai_chip_tickers: tuple = ("NVDA", "TSM")
    # Brake 2: drawdown from peak that forces a cut back to `brake_invested`.
    brake_drawdown: float = 0.06
    brake_invested: float = 0.70
    # Review lines for a single holding.
    review_day_drop: float = 0.07
    review_from_cost: float = 0.12
    # Do not buy a stock already up this much on the day.
    no_chase_day_gain: float = 0.08
    # Limit-price buffers above the reference price.
    steady_buffer: float = 0.01
    volatile_buffer: float = 0.02
    volatile_tickers: frozenset = field(
        default_factory=lambda: frozenset({"CRWD", "RKLB", "VRT", "SNDK"})
    )


CONTEST = ContestRules()
STRATEGY = StrategyRules()
