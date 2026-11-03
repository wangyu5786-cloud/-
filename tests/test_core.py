from pathlib import Path

import pytest

from wkuchallenge.config import CONTEST
from wkuchallenge.portfolio import Trade, build_positions, cash_after, load_prices, load_trades, rotation_days, snapshot
from wkuchallenge.rules import contest_score, limit_order, load_universe, off_list_penalty, risk_report, rotation_bonus_rate
from wkuchallenge.simulate import Strategy, simulate

DATA = Path(__file__).resolve().parents[1] / "data"


def test_average_cost_survives_partial_sell():
    trades = [
        Trade("2026-10-26", "TSM", "BUY", 16, 420.34),
        Trade("2026-10-28", "TSM", "BUY", 3, 438.01),
        Trade("2026-10-29", "TSM", "SELL", 9, 433.96),
    ]
    p = build_positions(trades)["TSM"]
    assert p.shares == 10
    assert p.avg_cost == pytest.approx((16 * 420.34 + 3 * 438.01) / 19)
    assert p.realised == pytest.approx(9 * (433.96 - p.avg_cost))


def test_overselling_is_rejected():
    with pytest.raises(ValueError):
        build_positions([Trade("d", "X", "BUY", 1, 10), Trade("d", "X", "SELL", 2, 10)])


@pytest.mark.parametrize("cutoff,price_file,cash,account", [
    ("2026-10-30", "prices_2026-10-30.csv", 42_903.29, 97_986.18),   # after the 10/30 close
    ("2026-11-02", "prices_2026-11-02.csv", 40_850.84, 96_959.94),   # after the 11/2 close
])
def test_real_log_reconciles_with_platform(cutoff, price_file, cash, account):
    trades = [t for t in load_trades(DATA / "trades.csv") if t.date <= cutoff]
    snap = snapshot(trades, load_prices(DATA / price_file), CONTEST.start_cash)
    assert cash_after(trades, CONTEST.start_cash) == pytest.approx(cash, abs=1.0)
    assert snap.account_value == pytest.approx(account, abs=1.0)


def test_every_trade_is_on_the_list():
    universe = load_universe(DATA / "universe.csv")
    assert len(universe) == 100
    assert {t.ticker for t in load_trades(DATA / "trades.csv")} <= universe


def test_rotation_days_skip_build_day():
    trades = load_trades(DATA / "trades.csv")
    assert len(rotation_days(trades, CONTEST.start_date)) == 5


@pytest.mark.parametrize("days,rate", [(0, 0), (1, 0.02), (2, 0.02), (3, 0.03), (4, 0.03), (5, 0.05), (12, 0.05)])
def test_rotation_tiers(days, rate):
    assert rotation_bonus_rate(days) == rate


def test_score_bonus_only_on_profit_and_penalty_capped():
    assert contest_score(110_000, 5) == pytest.approx(110_500)
    assert contest_score(95_000, 5) == 95_000
    assert off_list_penalty(500_000) == 10_000


def test_limit_order_buffers():
    steady = limit_order("NVDA", 10_000, prev_close=200, premarket=202)
    assert steady["limit"] == pytest.approx(204.02) and steady["shares"] == 49
    volatile = limit_order("VRT", 5_000, prev_close=230, live=225)
    assert volatile["reference"] == 225 and volatile["limit"] == pytest.approx(229.5)


def test_risk_report_flags_brake_and_review_line():
    rows = [dict(ticker="SNDK", weight=0.05, pnl_pct=-0.17), dict(ticker="NVDA", weight=0.30, pnl_pct=0.0)]
    msgs = " ".join(risk_report(rows, account_value=93_000, peak=100_000))
    assert "BRAKE 2" in msgs and "SNDK" in msgs and "single-stock cap" in msgs and "AI chips" in msgs


def test_simulation_more_risk_means_wider_outcomes():
    res = simulate([Strategy("low", 0.3, 1.2, 0.2), Strategy("high", 1.0, 2.0, 0.6)], 100_000, n=5_000)
    low, high = res
    assert high["p_top_3"] > low["p_top_3"]
    assert high["p_loss_8pct"] > low["p_loss_8pct"]
