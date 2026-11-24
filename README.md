# stock-trader

A realistic paper-trading experiment for a Danish investor, built on the **stock-analysis** skill from [alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills/tree/main/finance/skills/stock-analysis).

**Dashboard:** https://gustavwrisberg.github.io/stock-trader/

Three portfolios start with **10,000 kr** on a simulated **Saxo aktiesparekonto** and run every weekday after the US close:

| Portfolio | What it does |
|---|---|
| **Skill-scored** | Ranks 38 US-listed large caps half on the skill's sector-relative fundamental score and half on 12-month momentum. Holds 4 stocks and only buys stocks scoring 5+/10 with no red-flag veto. |
| **Momentum only** | The same rules without the skill. This is the control that shows whether the fundamentals add anything. |
| **S&P 500 index fund** | Buys Vanguard S&P 500 UCITS ETF (VUAA) once and holds it: what you would otherwise buy. |

## What makes it realistic

| | How it is modelled |
|---|---|
| Execution | Orders are decided after the close and fill at the **next day's open**, plus a 0.05% spread |
| Whole shares | No fractional shares. Leftover cash buys one extra share at a time for the most under-filled position |
| Commission | Saxo: 0.08%, minimum $1 on US stocks and €3 on the ETF |
| Currency | 0.25% on every DKK↔USD/EUR conversion; values in DKK at each day's rate |
| Dividends | Booked on the ex-date, with 15% US withholding (not refundable on an ASK) |
| Tax | ASK: 17% of each year's gain, paid at the turn of the year, losses carried forward; shares sold if cash is short |
| Splits | Share counts adjusted automatically |
| Turnover | Rebalances once a quarter; a holding is kept while it ranks in the top 8; no top-up trades |

Costs live in [`config/broker.json`](config/broker.json). Switch to Nordnet's prices (0.15%, minimum about $13) and you'll see why the broker choice matters with a small account.

## Why these settings

`research/backtest.py` (run with **Actions → Backtest**) tested 80 rule variants from 2012 to 2026 with the costs and tax above. The results are in [`research/backtest_results.md`](research/backtest_results.md) and the choice is in [`research/decision.json`](research/decision.json).

- The test universe is today's large caps, so every result is flattered by **survivorship bias**. The fair benchmark is an equal-weight hold of the same 38 stocks, and the chosen rules beat it in both 2012–18 and 2019–26.
- Quarterly rebalancing with a wide keep band cut costs to under 1% a year. Faster variants cost 2.5–4%.
- The 200-day trend filter did not help, so it is off.
- The chosen rules fell 42% at their worst, against 33% for the index fund. Expect real drawdowns.
- The skill's score **cannot be backtested** (there is no free point-in-time history of fundamentals), so this live run is the test: Skill-scored against Momentum only.

## How the skill is used

The skill is vendored, unmodified, in [`.claude/skills/stock-analysis`](.claude/skills/stock-analysis) (MIT licence).

1. **Weekly:** `trader/fundamentals.py` computes the metrics the skill asks for (ROCE, ROE, margins, 3-year cash conversion, accruals, leverage, interest cover, growth, dilution, P/E, FCF yield, EV/EBITDA; banks get ROA and P/B).
2. **Daily:** the skill's own `scripts/score.py` scores each company against its **sector** benchmarks. `config/universe.json` maps every ticker to a sector playbook.
3. **Red flags:** the skill's gates cap or veto a score. A veto sells at the next open on any day. One gate is detected automatically: cash flow below 50% of profit over 3 years. Others can be added in `config/flags.json` after a deep dive.

Because the skill lives in `.claude/skills/`, opening this repo in Claude Code lets you ask, for example, *"analyse NVDA with the stock-analysis skill"* for a full sourced report.

## Sources for the cost model (November 2026)

- Saxo prices for US stocks and ETFs: [home.saxo/da-dk/services](https://www.home.saxo/da-dk/services); 0.25% currency fee: [financer.dk review](https://financer.dk/review/saxoinvestor/)
- Nordnet: [prisliste](https://www.nordnet.dk/dk/kundeservice/prisliste/standard-bonus-pro), [valutaveksling 0.25%](https://www.nordnet.dk/marked/valutakurser)
- ASK 17% and 174,200 kr limit: [skat.dk](https://skat.dk/borger/aktier-og-andre-vaerdipapirer/aktiesparekonto), [Nordnet](https://www.nordnet.dk/blog/aktiesparekonto-skat-2026)
- Foreign stocks on an ASK and 15% dividend withholding: [Nordnet](https://www.nordnet.dk/dk/tjenester/konto-typer/aktiesparekonto), [Nordnet FAQ](https://www.nordnet.dk/faq/aktiesparekonto/skat-aktiesparekonto/hvordan-fungerer-udbytteskat-pa-en-aktiesparekonto)
- Danes can't buy US-domiciled ETFs; UCITS S&P 500 funds cost 0.07% a year: [tradedesk.dk](https://tradedesk.dk/etf/usa-sp500), [justETF](https://www.justetf.com/uk/how-to/sp-500-etfs.html)

## Caveats

- Data comes from Yahoo Finance via `yfinance`. The skill classes that as an aggregator: fine for a screen, never a source of record.
- The automated scores cover only the measurable parts of the skill, so they are labelled *indicative*.
- Tax is paid at the first run of the year; in reality it is drawn in February. Saxo's interest on cash is ignored.
- This is paper money and an experiment. It is not investment advice.

## Setup

1. **Pages:** Settings → Pages → Deploy from a branch → `main` / `docs`.
2. **Email (optional):** add the secrets `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REFRESH_TOKEN`, `EMAIL_FROM` and `EMAIL_TO`. You get an email on days with trades, dividends, tax or alerts, including the orders queued for the next open.
3. **Runs:** every weekday at 21:40 UTC, or Actions → *Daily paper trade* → Run workflow.

## Files

```
run.py                     daily entry point
trader/costs.py            Saxo/ASK cost and tax model
trader/portfolio.py        fills at the next open, whole shares, dividends, splits, tax
trader/engine.py           momentum, ranking, order decisions, stats
trader/fundamentals.py     statements -> skill metrics
trader/scoring.py          calls the skill's score.py
research/backtest.py       price-only backtest of the rules with real costs
config/                    universe, strategy, broker costs, manual red flags
data/                      bot state (portfolios, trades, equity, fundamentals cache, archive)
docs/                      the website (reads docs/data/dashboard.json)
```

Run `python run.py --demo` to try it offline with simulated data; it writes to `demo/`.
