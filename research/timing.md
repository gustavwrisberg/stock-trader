# Wait, ease in, or invest now? 80,000 kr, 5 years

Should you wait for a crash, or ease in? 80,000 kr towards a house in 5 years.

    python research/timing.py          # needs Yahoo Finance (Actions -> Backtest, script timing)

Every monthly start since 1993, 5-year horizon, S&P 500 total return in DKK (same fund costs, Lån & Spar
trading costs and 17% ASK tax as horizon.py; uninvested money earns 2% taxed at 37%):
  All at once     invest the 80,000 kr in month 1
  Over 6 months   invest 1/6 each month, the rest waits in savings
  Over 12 months  invest 1/12 each month
  Savings only    for reference

Each plan is also split by the starting situation: starts right after the market had fallen 10% or more from
its high (like November 2026), and all other starts. Not a forecast. Not investment advice.

Savings only ends at 85,169 kr. Monthly starts 1993-02-28 to 2021-12-31.

| plan           | starts                   |   windows |   median_kr |   worst_10pct_kr |   worst_kr |   pct_beat_savings |   pct_below_80k |   pct_lump_sum_did_better |
|:---------------|:-------------------------|----------:|------------:|-----------------:|-----------:|-------------------:|----------------:|--------------------------:|
| All at once    | All starts               |       347 |      133357 |            71414 |      53167 |                 74 |              22 |                       nan |
| All at once    | Starts after a 10%+ fall |       104 |      103607 |            67910 |      53167 |                 67 |              24 |                       nan |
| All at once    | Other starts             |       243 |      137031 |            72510 |      61228 |                 77 |              21 |                       nan |
| Over 6 months  | All starts               |       347 |      129626 |            69967 |      53006 |                 74 |              22 |                        69 |
| Over 6 months  | Starts after a 10%+ fall |       104 |      104534 |            66776 |      53006 |                 69 |              28 |                       nan |
| Over 6 months  | Other starts             |       243 |      132567 |            71781 |      62036 |                 77 |              20 |                       nan |
| Over 12 months | All starts               |       347 |      125969 |            68146 |      53641 |                 75 |              23 |                        76 |
| Over 12 months | Starts after a 10%+ fall |       104 |      109818 |            65202 |      53641 |                 68 |              30 |                       nan |
| Over 12 months | Other starts             |       243 |      128860 |            69858 |      60246 |                 78 |              20 |                       nan |
