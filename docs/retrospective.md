# Retrospective (written mid-contest, updated Nov 3, 2026)

## Timeline

| Date (US) | What we did | Why |
|---|---|---|
| Oct 26 | Bought XOM and TSM | Opened with an energy hedge plus an AI foundry name, about 14% invested |
| Oct 27 | Bought NVDA and CRWD | AI compute core and cybersecurity |
| Oct 28 | Topped up TSM; bought BRK.B, GEV and SNDK | Moved to the aggressive plan after the model run; SNDK was an earnings bet |
| Oct 29 | A teammate trimmed TSM; we bought GOOGL | GOOGL fell 12.6% that day, its worst day on record |
| Oct 30 | Bought BRK.B and VRT (GTC limit at $230) | The semiconductor index fell 7.2%. We added defence and caught VRT on the dip |
| Nov 2 | Bought 5 TSM | Fifth rotation day, which locks in the top 5% bonus tier |

## What worked

- **Hedges did their job.** On Oct 30 the account fell 1.8% (from about $99,785 to $97,986). Over the same day the Nasdaq-100 fell 3.5% and the semiconductor index fell 7.2%. XOM (+2%, a record high), BRK.B and 44% cash cushioned the drop.
- **Patient limits on dips.** VRT filled at about $229.56 on a GTC limit and was in profit at the close.
- **Writing rules down before trading.** A fixed limit formula, position caps and a drawdown brake kept arguments short when prices moved fast.

## What went wrong, and the fix

| Mistake | Fix now in the process / code |
|---|---|
| The first NVDA limit was set from the prior close and never filled on a gap up | `limit_order()` uses max(close, premarket), or the live price after the open, plus a volatility-based buffer |
| Orders went into the platform's default game instead of the contest | A checklist step: confirm the game name before every order |
| An earnings date (XOM) was missed when planning | The full event calendar is checked again before each week |
| A limit was proposed from a stale price (VRT $244 when it already traded at $236) | Fetch the latest price before writing any order; never reuse a level from earlier notes |
| SNDK was bought into earnings and fell despite beating estimates | The team decided to hold with a 13% trailing stop rather than sell at the low. Lesson: size earnings bets smaller |

## Still open

- We are 58% invested against an 89% target, and the rank is 117 of 147 (Nov 2). The remaining weeks will decide whether the aggressive plan pays off.
- This file will be updated after Nov 20 with the final result.
