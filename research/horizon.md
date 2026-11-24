# How many years before investing beats saving? (80,000 kr towards a house deposit)

Saving 80,000 kr towards a house deposit: how many years until investing beats a savings account?

    python research/horizon.py         # needs Yahoo Finance (Actions -> Backtest, script horizon)

For every horizon from 1 to 10 years, every monthly start since 1993 is tested:
  Savings  2.0% interest a year, taxed at 37% as capital income (best accounts paid ~2.3% with a year's
           binding in autumn 2026; the central bank rate was 2.1%)
  Index    a Danish-listed global/US index fund on an aktiesparekonto (0.40% a year, 0.10% min 29 kr per
           trade at Lån & Spar, 17% tax on each year's gain, losses carried forward)
  Glide    the index fund, moved to savings in equal monthly steps over the final 2 years (final year for
           horizons up to 3 years), so a late crash can only hit part of the money

Index history: S&P 500 (SPY) total return in DKK from 1996 (USD before), the longest free series. US stocks
did unusually well in this period, so the index results are flattering. A range of what happened, not a
forecast. Not investment advice.

Monthly windows from 1993-02-28 to 2026-11-30.

|   years | plan                         |   windows |   savings_kr |   median_kr |   worst_10pct_kr |   worst_kr |   pct_beat_savings |   pct_below_80k |   pct_lost_over_20pct |
|--------:|:-----------------------------|----------:|-------------:|------------:|-----------------:|-----------:|-------------------:|----------------:|----------------------:|
|       1 | Index fund                   |       395 |        81008 |       88401 |            69273 |      52413 |                 77 |              19 |                     6 |
|       2 | Index fund                   |       383 |        82029 |       99256 |            65979 |      45298 |                 83 |              16 |                     8 |
|       2 | Index fund, glide to savings |       383 |        82029 |       93762 |            68402 |      51174 |                 81 |              17 |                     8 |
|       3 | Index fund                   |       371 |        83062 |      110268 |            65857 |      45475 |                 79 |              19 |                     9 |
|       3 | Index fund, glide to savings |       371 |        83062 |      104234 |            64048 |      49081 |                 81 |              17 |                    10 |
|       4 | Index fund                   |       359 |        84109 |      118735 |            65883 |      52939 |                 75 |              23 |                     8 |
|       4 | Index fund, glide to savings |       359 |        84109 |      111310 |            63400 |      53644 |                 80 |              19 |                    11 |
|       5 | Index fund                   |       347 |        85169 |      133357 |            71414 |      53167 |                 74 |              22 |                     3 |
|       5 | Index fund, glide to savings |       347 |        85169 |      122276 |            67540 |      59760 |                 74 |              23 |                     7 |
|       6 | Index fund                   |       335 |        86242 |      140867 |            77800 |      69407 |                 77 |              13 |                     0 |
|       6 | Index fund, glide to savings |       335 |        86242 |      135786 |            72406 |      66370 |                 73 |              20 |                     0 |
|       7 | Index fund                   |       323 |        87328 |      158586 |            82441 |      56286 |                 84 |               6 |                     1 |
|       7 | Index fund, glide to savings |       323 |        87328 |      144995 |            80253 |      72974 |                 74 |              10 |                     0 |
|       8 | Index fund                   |       311 |        88429 |      145527 |            88114 |      51825 |                 90 |               9 |                     4 |
|       8 | Index fund, glide to savings |       311 |        88429 |      156028 |            83096 |      69978 |                 83 |               9 |                     0 |
|       9 | Index fund                   |       299 |        89543 |      151848 |            80273 |      45660 |                 88 |              10 |                     5 |
|       9 | Index fund, glide to savings |       299 |        89543 |      142778 |            80710 |      59116 |                 87 |              10 |                     3 |
|      10 | Index fund                   |       287 |        90671 |      166766 |            81243 |      52482 |                 85 |              10 |                     5 |
|      10 | Index fund, glide to savings |       287 |        90671 |      154474 |            79362 |      55881 |                 87 |              10 |                     5 |
