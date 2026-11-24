# stock-trader

**Does picking stocks with an AI analysis skill beat just buying an index fund, once every real cost is paid?**

This repo runs that experiment every weekday with paper money. Three portfolios start with 10,000 kr each on a simulated Saxo *aktiesparekonto*, the Danish tax-advantaged share account. They pay the same commissions, currency charges and taxes a Danish investor would, and their results are published to a website.

**Dashboard:** https://gustavwrisberg.github.io/stock-trader/

> Paper money only. This is an experiment, not investment advice.

## The three contenders

| Portfolio | How it picks |
|---|---|
| **Skill-scored** | Scores 38 large US-listed companies with the [stock-analysis skill](https://github.com/alirezarezvani/claude-skills/tree/main/finance/skills/stock-analysis), which grades each company's fundamentals against its own sector. Ranks them half on that score and half on 12-month price momentum, and holds the top 4. |
| **Momentum only** | The same rules without the skill. If Skill-scored doesn't beat this one, the skill isn't adding anything. |
| **S&P 500 index fund** | Buys Vanguard S&P 500 UCITS ETF once and holds it. This is the "do nothing" alternative every strategy has to beat. |

## How it works

Every weekday at 22:40 Danish time, after the US market closes, GitHub Actions runs `run.py`:

1. Downloads prices, dividends, stock splits and the USD/DKK rate.
2. Fills yesterday's orders at **today's opening price**, never at the price the decision was made on.
3. Once a week, refreshes each company's financial statements and scores them with the skill's own `score.py`.
4. Once a **quarter**, decides what to buy and sell for the next open. On other days it only sells if a company hits a red flag.
5. Updates the website and sends an email when anything happened.

### Costs and tax included

| | Modelled as |
|---|---|
| Commission | Saxo: 0.08%, minimum $1 per US stock trade and €3 per fund trade |
| Currency exchange | 0.25% each time kroner become dollars or back |
| Spread | 0.05% on every market order |
| Whole shares only | No fractional shares; a stock is skipped if one share costs more than its slot |
| Dividends | 15% kept by the US tax authority, not refundable on an aktiesparekonto |
| Tax | 17% of each year's gain, unsold shares included; losses carry forward |

All of these settings are in [`config/broker.json`](config/broker.json).

### Why these rules

Before going live, 80 variants of the rules were backtested on 2012–2026 prices with the costs above ([results](research/backtest_results.md), [decision](research/decision.json)). Trading once a quarter kept costs under 1% a year, while monthly trading cost 2.5–4%. Two caveats matter:

- The backtest only uses today's large companies, so every result looks better than it would have in real time. Compare the rules with each other, not with the index fund.
- The skill's score can't be backtested, because there's no free history of what companies reported at each past date. This live run is the real test.

## How to use it

**Check in when you like.** The dashboard's headline tells you who is ahead. "What happened today" lists trades, dividends and the orders waiting for the next open. Most days nothing trades: buying and selling happens once a quarter.

**Read your email.** Add the secrets below and you'll get an email on days with trades, dividends, tax or alerts (a holding falls 3% or more, or hits a red flag).

**Look at the scoreboard.** Every stock the bot watches is there. Open a row to see the skill's scores by category and the numbers behind them, compared with the company's sector.

**Dig into a company with Claude Code.** The skill is included in this repo, so open the repo in Claude Code and ask something like *"analyse NVDA with the stock-analysis skill"*. You'll get a full report built from the company's own filings. Save it to `analyses/`. If it finds a serious problem, such as a qualified audit or restated accounts, add it to [`config/flags.json`](config/flags.json) and the bot will respect it from the next run.

**Change the experiment.** The usual edits:

| To change | Edit |
|---|---|
| The broker's prices (for example to Nordnet) | `config/broker.json` |
| Number of stocks, rebalance frequency, skill weight | `config/strategy.json` |
| Which companies it watches | `config/universe.json` |

Costs apply from the next run. Changing the number of stocks or the starting amount works best with a fresh start; ask Claude to restart the portfolios, and the old history is archived, not deleted.

**Re-test the rules.** Actions → **Backtest** → Run workflow. It takes about 5 minutes and updates `research/backtest_results.md`.

**Run it by hand.** Actions → **Daily paper trade** → Run workflow. Running twice on the same day is safe; it won't trade twice.

**Judge it fairly.** Give it at least a year, ideally longer. A few months of results is mostly luck. The questions that matter: does Skill-scored beat Momentum only (does the skill help?), and does either beat the index fund after costs and tax?

## Trading on a Saxo practice account

`execute_saxo.py` copies the Skill-scored portfolio onto a Saxo account. It runs as the **Saxo practice trading** workflow, on weekdays shortly after the US market opens. The default is Saxo's practice system: a simulated account with fake money.

- **Reconcile, don't replay.** Each run compares what the paper model wants to hold with what Saxo actually holds, and trades only the difference. A missed run is caught up next time; nothing is doubled.
- **Safety checks.** Every order is pre-checked by Saxo, labelled so it can't be sent twice, and must pass the limits in [`config/saxo.json`](config/saxo.json): per order, per run, in total, and a guard against prices that moved more than 5% from the model's. Differences under 500 kr are left alone, so rounding never costs a minimum fee.
- **Off switch.** Set `"enabled": false` in `config/saxo.json`, or `"dry_run": true` to only see the plan.
- **Live money is locked.** It needs `"environment": "live"` and a secret `SAXO_ALLOW_LIVE` containing an exact phrase.
- **Log.** Every order is recorded in `data/saxo/executions.csv`, and `data/saxo/reconcile.json` shows model against Saxo.

**Access key.** Saxo's keys are short-lived. Personal customers can't get a never-expiring key, so a person has to log in now and then. For the practice account, use the 24-hour token:

1. Go to [developer.saxo/openapi/token](https://www.developer.saxo/openapi/token) while logged in and copy the token.
2. In this repo, open Settings → Secrets and variables → Actions → New repository secret. Name it `SAXO_TOKEN` and paste the token.
3. Go to Actions → **Saxo practice trading** → Run workflow. Leave "Only show the plan" ticked the first time.

The strategy trades about once a quarter. When orders are waiting and the token has expired, you get an email asking you to refresh it.

## Setup

1. **Website:** Settings → Pages → Deploy from a branch → `main`, folder `/docs`.
2. **Email (optional):** Settings → Secrets and variables → Actions. Add `EMAIL_FROM` (your Gmail address), `GMAIL_APP_PASSWORD` (a 16-letter app password from myaccount.google.com/apppasswords, needs 2-step verification) and optionally `EMAIL_TO`. Then run the **Test email** workflow from the Actions tab. (The older `GMAIL_CLIENT_ID`/`GMAIL_CLIENT_SECRET`/`GMAIL_REFRESH_TOKEN` OAuth setup still works if no app password is set.)
3. **Offline test:** `pip install -r requirements.txt`, then `python run.py --demo` runs on simulated data and writes to `demo/`.

## What's in the repo

```
run.py                     the daily run
trader/costs.py            Saxo fees, currency charges and aktiesparekonto tax
trader/portfolio.py        next-open fills, whole shares, dividends, splits, tax payments
trader/engine.py           momentum, ranking and order decisions
trader/fundamentals.py     financial statements -> the skill's metrics
trader/scoring.py          runs the skill's score.py
research/backtest.py       backtest of the rules with real costs
execute_saxo.py            mirrors the paper portfolio onto a Saxo account (practice by default)
trader/saxo.py             minimal Saxo OpenAPI client
config/                    companies, strategy, broker costs, manual red flags
data/                      the bot's state and history (written by the bot)
docs/                      the website
.claude/skills/            the stock-analysis skill, unmodified (MIT licence)
```

## Sources for the cost model (November 2026)

- Saxo: [prices](https://www.home.saxo/da-dk/services), [0.25% currency fee](https://financer.dk/review/saxoinvestor/)
- Nordnet: [price list](https://www.nordnet.dk/dk/kundeservice/prisliste/standard-bonus-pro), [currency exchange](https://www.nordnet.dk/marked/valutakurser)
- Aktiesparekonto, 17% tax and 174,200 kr limit: [skat.dk](https://skat.dk/borger/aktier-og-andre-vaerdipapirer/aktiesparekonto), [Nordnet](https://www.nordnet.dk/blog/aktiesparekonto-skat-2026)
- Foreign stocks and dividend tax on an aktiesparekonto: [Nordnet](https://www.nordnet.dk/dk/tjenester/konto-typer/aktiesparekonto), [Nordnet FAQ](https://www.nordnet.dk/faq/aktiesparekonto/skat-aktiesparekonto/hvordan-fungerer-udbytteskat-pa-en-aktiesparekonto)
- Why Danes buy UCITS index funds: [tradedesk.dk](https://tradedesk.dk/etf/usa-sp500), [justETF](https://www.justetf.com/uk/how-to/sp-500-etfs.html)

## Limitations

- Prices and statements come from Yahoo Finance via `yfinance`. The skill treats that as an unverified aggregator: fine for a screen, not for a real decision.
- Automated scores cover only the measurable parts of the skill (no judgement on moat, governance or management), so they are labelled *indicative*.
- Tax is paid at the first run of the year; in reality it is drawn in February. Interest on cash is ignored.
- Costs are researched estimates, not a broker's quote.
