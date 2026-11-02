"""Monte Carlo model used to choose how aggressive to be.

The question it answers: over the remaining trading days, how do different
levels of exposure (share invested), market sensitivity (beta) and
concentration (idiosyncratic volatility) change the odds of finishing near
the top versus losing badly?

Model, per simulated contest:
  * one shared market return  M ~ N(mu*T, sd*sqrt(T))
  * our return               r = expo * (beta*M + idio*sqrt(T)*Z)
  * K competitors drawn from a mix of styles, scored the same way
  * score = value + rotation bonus on profit

It is deliberately simple. It ignores fat tails, sector correlation between
us and competitors, and path-dependent rules such as the drawdown brake, so
the outputs are best read as relative comparisons between strategies.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class MarketModel:
    days: int = 18
    mu: float = 0.08          # annual market drift
    sd: float = 0.18          # annual market volatility
    competitors: int = 123
    # competitor styles: (exposure, beta, idio vol) and their mix weights
    styles: tuple = ((0.4, 1.1, 0.25), (0.7, 1.2, 0.25), (1.0, 1.3, 0.30), (1.0, 1.8, 0.60))
    style_mix: tuple = (0.15, 0.25, 0.40, 0.20)
    bonus_rate: float = 0.05
    start_cash: float = 100_000.0


@dataclass(frozen=True)
class Strategy:
    name: str
    exposure: float
    beta: float
    idio: float


def simulate(strategies: list[Strategy], start_value: float, model: MarketModel = MarketModel(),
             n: int = 50_000, seed: int = 7) -> list[dict]:
    rng = np.random.default_rng(seed)
    T = model.days / 252
    M = rng.normal(model.mu * T, model.sd * np.sqrt(T), n)

    pars = np.array(model.styles)[rng.choice(len(model.styles), size=(n, model.competitors), p=model.style_mix)]
    expo = pars[..., 0] * rng.uniform(0.8, 1.0, (n, model.competitors))
    comp_r = expo * (pars[..., 1] * M[:, None] + rng.normal(0, 1, (n, model.competitors)) * pars[..., 2] * np.sqrt(T))
    comp_v = model.start_cash * (1 + rng.normal(0, 0.004, (n, model.competitors))) * (1 + comp_r)
    comp_s = comp_v + np.maximum(comp_v - model.start_cash, 0) * model.bonus_rate

    results = []
    Z = rng.normal(0, 1, n)  # same idiosyncratic draws for every strategy -> fair comparison
    for s in strategies:
        r = s.exposure * (s.beta * M + s.idio * np.sqrt(T) * Z)
        v = start_value * (1 + r)
        score = v + np.maximum(v - model.start_cash, 0) * model.bonus_rate
        rank = 1 + (comp_s > score[:, None]).sum(1)
        results.append(dict(
            strategy=s.name,
            expected_score=float(score.mean()),
            p_loss_8pct=float((v < model.start_cash * 0.92).mean()),
            p_bottom_20=float((rank > model.competitors + 1 - 20).mean()),
            p_top_10=float((rank <= 10).mean()),
            p_top_3=float((rank <= 3).mean()),
            p5_score=float(np.percentile(score, 5)),
        ))
    return results


DEFAULT_STRATEGIES = [
    Strategy("Conservative: ~30% invested", 0.30, 1.4, 0.25),
    Strategy("Original plan: ~60% invested", 0.60, 1.4, 0.25),
    Strategy("Aggressive: ~89% in 5-6 names", 0.89, 1.6, 0.35),
    Strategy("All-in: 2-3 high-vol names", 1.00, 2.0, 0.60),
]
