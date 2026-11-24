# stock-trader

A daily paper-trading experiment built on the **stock-analysis** skill from [alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills/tree/main/finance/skills/stock-analysis).

**Dashboard:** https://gustavwrisberg.github.io/stock-trader/

Three portfolios start with $10,000 each and run every weekday after the US close:

| Portfolio | How it picks |
|---|---|
| **Skill-scored** | Ranks 38 large caps half on the skill's sector-relative fundamental score, half on 12-month momentum. Only buys stocks scoring 5+/10 with no red-flag veto and a price above the 200-day average. |
| **Momentum only** | Same universe and rules, but ignores fundamentals. This is the control that shows whether the skill adds anything. |
| **S&P 500** | Buy and hold SPY. |

Each portfolio holds 6 stocks at equal weight and keeps a holding while it ranks in the top 10. Weights reset on the first run of each month, and every trade costs 0.10%.

## How the skill is used

The skill is vendored, unmodified, in [`.claude/skills/stock-analysis`](.claude/skills/stock-analysis) (MIT licence).

1. **Weekly:** `trader/fundamentals.py` pulls annual statements and computes the metrics the skill asks for: ROCE, ROE, margins, 3-year cash conversion, accruals, leverage, interest cover, growth, dilution, P/E, FCF yield and EV/EBITDA. Banks get the skill's bank set (ROA, ROE, P/B) instead.
2. **Daily:** the skill's own `scripts/score.py` scores each company against its **sector** benchmarks (`config/universe.json` maps every ticker to a sector playbook). Valuation metrics are refreshed with each day's price.
3. **Red flags:** the skill's gates cap or veto scores. One is detected automatically: 3-year operating cash flow below 50% of profit. Others can be added by hand in `config/flags.json` after a deep dive.

### Deep dives with Claude Code

Because the skill lives in `.claude/skills/`, opening this repo in Claude Code makes it available. Ask, for example, *"analyse NVDA with the stock-analysis skill"* for a full sourced report. Save it in `analyses/`. If it finds a red flag such as a qualified audit or a restatement, record it in `config/flags.json` and the bot will respect it from the next run.

## Honest caveats

- Data comes from Yahoo Finance via `yfinance`. The skill classes that as an *aggregator*: fine for a screen, never a source of record.
- The automated scores cover only the measurable parts of the skill. Moat, governance and management judgement are not automated, so every score is labelled *indicative*.
- This is paper money and an experiment. It is not investment advice.

## Setup

1. **Pages:** Settings → Pages → Deploy from a branch → `main` / `docs`.
2. **Email alerts (optional):** add the same secrets as `paper-trader`: `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REFRESH_TOKEN`, `EMAIL_FROM`, `EMAIL_TO`. You get an email on days with trades or alerts (a holding falls 3%+, breaks its 50-day average, or hits a veto).
3. **First run:** Actions → *Daily paper trade* → Run workflow. After that it runs every weekday at 21:40 UTC.

## Files

```
run.py                     daily entry point
trader/fundamentals.py     statements -> skill metrics
trader/scoring.py          calls the skill's score.py
trader/engine.py           momentum, ranking, portfolios, stats
config/universe.json       tickers and their sector playbooks
config/strategy.json       holdings, keep band, costs, weights
config/flags.json          manual red flags from deep dives
data/                      state: portfolios, trades, equity, fundamentals cache
docs/                      the website (reads docs/data/dashboard.json)
```

To try it offline with simulated data, run `python run.py --demo`; it writes to `demo/`.
