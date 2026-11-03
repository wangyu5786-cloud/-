"""Command line: python -m wkuchallenge <command>

  status    holdings, P&L, invested share, rule warnings, contest score
  limit     limit price and share count for a planned buy
  simulate  Monte Carlo comparison of strategies
  charts    write the README charts to reports/
"""
from __future__ import annotations

import argparse
from pathlib import Path

from .config import CONTEST, STRATEGY
from .portfolio import load_prices, load_trades, rotation_days, snapshot
from .rules import contest_score, limit_order, load_universe, risk_report

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"


def _snap(args):
    trades = load_trades(args.trades)
    prices = load_prices(args.prices)
    return trades, snapshot(trades, prices, CONTEST.start_cash)


def cmd_status(args) -> None:
    trades, snap = _snap(args)
    universe = load_universe(DATA / "universe.csv")
    off_list = sorted({t.ticker for t in trades} - universe)

    print(f"{'Ticker':<7}{'Shares':>7}{'Avg cost':>11}{'Price':>10}{'Value':>11}{'P&L':>10}{'P&L %':>8}{'Weight':>8}")
    for r in snap.rows:
        print(f"{r['ticker']:<7}{r['shares']:>7}{r['avg_cost']:>11.2f}{r['price']:>10.2f}{r['value']:>11,.0f}"
              f"{r['pnl']:>10,.0f}{r['pnl_pct']:>8.1%}{r['weight']:>8.1%}")
    days = rotation_days(trades, CONTEST.start_date)
    print(f"\nCash {snap.cash:,.2f} | Account {snap.account_value:,.2f} | Invested {snap.invested:.0%} "
          f"(target {STRATEGY.target_invested:.0%})")
    print(f"Rotation days {len(days)}: {', '.join(days)}")
    print(f"Contest score now: {contest_score(snap.account_value, len(days)):,.2f}")
    print("Off-list tickers: " + (", ".join(off_list) if off_list else "none"))
    warnings = risk_report(snap.rows, snap.account_value, args.peak)
    print("\nRule checks:")
    print("\n".join(f"  ! {w}" for w in warnings) if warnings else "  all clear")


def cmd_limit(args) -> None:
    o = limit_order(args.ticker.upper(), args.budget, args.prev_close, args.premarket, args.live)
    print(f"{o['ticker']}: reference {o['reference']:.2f} +{o['buffer']:.0%} -> limit {o['limit']:.2f}, "
          f"{o['shares']} shares, about ${o['cost']:,.0f}")


def cmd_simulate(args) -> None:
    from .simulate import DEFAULT_STRATEGIES, MarketModel, simulate

    res = simulate(DEFAULT_STRATEGIES, args.start, MarketModel(days=args.days), n=args.n)
    print(f"{'Strategy':<34}{'E[score]':>10}{'Lose >8%':>10}{'Bottom 20':>11}{'Top 10':>8}{'Top 3':>7}")
    for r in res:
        print(f"{r['strategy']:<34}{r['expected_score']:>10,.0f}{r['p_loss_8pct']:>10.1%}{r['p_bottom_20']:>11.1%}"
              f"{r['p_top_10']:>8.1%}{r['p_top_3']:>7.1%}")


def cmd_charts(args) -> None:
    from .report import allocation_chart, pnl_chart

    _, snap = _snap(args)
    out = ROOT / "reports"
    out.mkdir(exist_ok=True)
    p1 = pnl_chart(snap.rows, STRATEGY.review_from_cost, out / "pnl_vs_cost.png", "Holdings vs average cost")
    p2 = allocation_chart(snap.rows, snap.cash, out / "allocation.png",
                          f"Allocation - {snap.invested:.0%} invested")
    print(f"wrote {p1}\nwrote {p2}")


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(prog="wkuchallenge", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    for name, fn in (("status", cmd_status), ("charts", cmd_charts)):
        p = sub.add_parser(name)
        p.add_argument("--trades", default=DATA / "trades.csv")
        p.add_argument("--prices", default=DATA / "prices_2026-11-02.csv")
        p.add_argument("--peak", type=float, default=100_400.0, help="highest account value so far")
        p.set_defaults(fn=fn)

    p = sub.add_parser("limit")
    p.add_argument("ticker")
    p.add_argument("budget", type=float)
    p.add_argument("--prev-close", type=float, required=True)
    p.add_argument("--premarket", type=float)
    p.add_argument("--live", type=float)
    p.set_defaults(fn=cmd_limit)

    p = sub.add_parser("simulate")
    p.add_argument("--start", type=float, default=96_959.94)
    p.add_argument("--days", type=int, default=14)
    p.add_argument("--n", type=int, default=50_000)
    p.set_defaults(fn=cmd_simulate)

    args = ap.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
