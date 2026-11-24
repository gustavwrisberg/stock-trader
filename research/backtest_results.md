# Backtest results

Price-only backtest of the trading rules, with real Danish costs, to choose the parameters.

    python research/backtest.py            # needs Yahoo Finance access (run it via GitHub Actions)

What it can and cannot tell you
- It tests the parts that depend only on prices: momentum ranking, the 200-day trend filter,
  number of holdings, rebalance frequency, keep band, whole shares, fees, FX and tax drag.
- It CANNOT test the skill's fundamental score: free data has no point-in-time history of
  statements, and using today's statements on old prices would be look-ahead bias.
- The universe is today's large caps, so returns are flattered by survivorship bias. Use the
  results to compare variants with each other, not as a forecast.

Period 2012-01-03 to 2026-11-23, values in DKK after Saxo costs and 17% ASK tax.

## Starting with 10,000 kr (sorted by Sharpe)

| name                                                          |   cagr_pct |   sharpe |   max_drawdown_pct |   worst_year_pct |   costs_pct_per_year |   turnover_x_per_year |
|:--------------------------------------------------------------|-----------:|---------:|-------------------:|-----------------:|---------------------:|----------------------:|
| 3 stocks, monthly, keep top 6, trend filter, 6-1m momentum    |      32.38 |     1.06 |              -44.2 |            -30.8 |                63.34 |                 83.17 |
| 3 stocks, quarterly, keep top 3, trend filter, 6-1m momentum  |      31.39 |     1.05 |              -43.1 |            -25.6 |                36.68 |                 48.12 |
| 3 stocks, quarterly, keep top 3, no filter, 6-1m momentum     |      31    |     1.04 |              -43   |            -25.6 |                38.41 |                 50.38 |
| 4 stocks, quarterly, keep top 8, no filter, 12-1m momentum    |      27.58 |     1.04 |              -33.4 |            -10.2 |                10.13 |                 13.16 |
| 6 stocks, quarterly, keep top 12, no filter, 12-1m momentum   |      26.31 |     1.04 |              -31.5 |             -3.9 |                 5.75 |                  7.17 |
| 4 stocks, monthly, keep top 8, no filter, 6-1m momentum       |      28.81 |     1.02 |              -37.4 |            -18.7 |                37.79 |                 49.39 |
| 4 stocks, monthly, keep top 8, trend filter, 6-1m momentum    |      27.96 |     1.01 |              -37   |            -17.9 |                36.71 |                 48.02 |
| 8 stocks, quarterly, keep top 16, no filter, 12-1m momentum   |      23.12 |     1.01 |              -28.3 |             -7.8 |                 4.7  |                  5.68 |
| 5 stocks, monthly, keep top 10, NO COSTS (reference)          |      26.99 |     1.01 |              -33.8 |             -8.6 |                 0    |                 17.56 |
| 8 stocks, monthly, keep top 8, trend filter, 6-1m momentum    |      24.24 |     1.01 |              -38.3 |            -15.6 |                29.59 |                 36.82 |
| 4 stocks, monthly, keep top 8, no filter, 12-1m momentum      |      29.21 |     1    |              -33.6 |             -6.7 |                16.72 |                 21.81 |
| 5 stocks, quarterly, keep top 10, no filter, 12-1m momentum   |      26.46 |     1    |              -32.2 |             -5.3 |                 6.37 |                  8.09 |
| 6 stocks, quarterly, keep top 6, no filter, 6-1m momentum     |      24.63 |     1    |              -38.8 |            -16.8 |                16.96 |                 21.61 |
| 8 stocks, monthly, keep top 16, no filter, 12-1m momentum     |      24.21 |     0.99 |              -33.1 |             -8.9 |                 5.83 |                  7.04 |
| 6 stocks, quarterly, keep top 6, trend filter, 6-1m momentum  |      24.46 |     0.99 |              -38.5 |            -16.9 |                16.84 |                 21.51 |
| 6 stocks, quarterly, keep top 6, no filter, 12-1m momentum    |      24.76 |     0.99 |              -28.9 |              2.9 |                 9.88 |                 12.46 |
| 4 stocks, quarterly, keep top 8, trend filter, 12-1m momentum |      25.92 |     0.99 |              -35.2 |             -2.4 |                 9.21 |                 11.96 |
| 3 stocks, quarterly, keep top 3, no filter, 12-1m momentum    |      28.49 |     0.98 |              -36.4 |             -7.1 |                14.63 |                 19.11 |
| 8 stocks, monthly, keep top 8, no filter, 6-1m momentum       |      23.55 |     0.98 |              -39   |            -17.9 |                28.84 |                 35.65 |
| 3 stocks, quarterly, keep top 6, no filter, 6-1m momentum     |      27.94 |     0.98 |              -42.8 |            -25   |                21.44 |                 28.04 |
| 5 stocks, monthly, keep top 10, no filter, 12-1m momentum     |      26.77 |     0.98 |              -32.1 |             -5.2 |                11.26 |                 14.46 |
| 5 stocks, quarterly, keep top 5, no filter, 6-1m momentum     |      25.25 |     0.98 |              -40.8 |            -22.8 |                19.94 |                 25.73 |
| 3 stocks, monthly, keep top 6, no filter, 6-1m momentum       |      28.89 |     0.98 |              -47.1 |            -35.2 |                46.82 |                 61.41 |
| 5 stocks, monthly, keep top 10, no filter, 6-1m momentum      |      25.73 |     0.97 |              -36.4 |            -15.6 |                25.4  |                 32.91 |
| 5 stocks, quarterly, keep top 5, trend filter, 6-1m momentum  |      24.85 |     0.97 |              -40.7 |            -22.9 |                18.92 |                 24.44 |

## Starting with 100,000 kr (sorted by Sharpe)

| name                                                          |   cagr_pct |   sharpe |   max_drawdown_pct |   worst_year_pct |   costs_pct_per_year |   turnover_x_per_year |
|:--------------------------------------------------------------|-----------:|---------:|-------------------:|-----------------:|---------------------:|----------------------:|
| 3 stocks, monthly, keep top 6, trend filter, 6-1m momentum    |      32.58 |     1.07 |              -44.3 |            -31   |                65.11 |                 85.63 |
| 3 stocks, quarterly, keep top 3, trend filter, 6-1m momentum  |      31.57 |     1.05 |              -43.2 |            -25.6 |                37.54 |                 49.37 |
| 6 stocks, quarterly, keep top 12, no filter, 12-1m momentum   |      26.76 |     1.05 |              -31.9 |             -4.4 |                 5.72 |                  7.53 |
| 3 stocks, quarterly, keep top 3, no filter, 6-1m momentum     |      31.25 |     1.04 |              -43.2 |            -25.6 |                39.67 |                 52.17 |
| 4 stocks, quarterly, keep top 8, no filter, 12-1m momentum    |      27.35 |     1.03 |              -33.5 |             -9.9 |                 9.77 |                 12.85 |
| 4 stocks, monthly, keep top 8, no filter, 6-1m momentum       |      28.82 |     1.02 |              -37.3 |            -18.7 |                38.96 |                 51.23 |
| 5 stocks, monthly, keep top 10, NO COSTS (reference)          |      27.25 |     1.01 |              -33.9 |             -8.6 |                 0    |                 18.37 |
| 4 stocks, monthly, keep top 8, no filter, 12-1m momentum      |      29.24 |     1    |              -34   |             -6.7 |                16.64 |                 21.88 |
| 8 stocks, monthly, keep top 16, no filter, 12-1m momentum     |      24.69 |     1    |              -33.2 |             -8   |                 5.73 |                  7.54 |
| 5 stocks, quarterly, keep top 10, no filter, 12-1m momentum   |      26.82 |     1    |              -32.4 |             -5.4 |                 6.47 |                  8.51 |
| 4 stocks, monthly, keep top 8, trend filter, 6-1m momentum    |      27.77 |     1    |              -37.3 |            -18.1 |                35.87 |                 47.18 |
| 6 stocks, quarterly, keep top 6, no filter, 6-1m momentum     |      24.84 |     1    |              -39   |            -18.1 |                17.2  |                 22.62 |
| 8 stocks, quarterly, keep top 16, no filter, 6-1m momentum    |      24    |     1    |              -31.8 |             -9.6 |                 8.5  |                 11.17 |
| 3 stocks, monthly, keep top 6, no filter, 6-1m momentum       |      29.13 |     0.99 |              -47.4 |            -35.5 |                48.52 |                 63.8  |
| 3 stocks, quarterly, keep top 3, no filter, 12-1m momentum    |      28.91 |     0.99 |              -36.8 |             -7.2 |                15.21 |                 20    |
| 5 stocks, monthly, keep top 10, no filter, 12-1m momentum     |      27.04 |     0.99 |              -32.1 |             -5.1 |                11.44 |                 15.05 |
| 3 stocks, quarterly, keep top 3, trend filter, 12-1m momentum |      28.13 |     0.98 |              -36.8 |             -4.8 |                14.89 |                 19.58 |
| 3 stocks, quarterly, keep top 6, trend filter, 6-1m momentum  |      27.88 |     0.98 |              -43.2 |            -24.8 |                19.82 |                 26.06 |
| 6 stocks, quarterly, keep top 6, no filter, 12-1m momentum    |      24.35 |     0.98 |              -29.3 |              3.3 |                 9.26 |                 12.17 |
| 6 stocks, quarterly, keep top 6, trend filter, 6-1m momentum  |      24.3  |     0.98 |              -39   |            -18.1 |                16.53 |                 21.74 |
| 3 stocks, quarterly, keep top 6, no filter, 6-1m momentum     |      27.96 |     0.98 |              -43.2 |            -24.8 |                21.93 |                 28.84 |
| 8 stocks, quarterly, keep top 16, no filter, 12-1m momentum   |      22.8  |     0.98 |              -28.4 |             -7.2 |                 4.21 |                  5.53 |
| 5 stocks, monthly, keep top 10, no filter, 6-1m momentum      |      26.11 |     0.98 |              -36.6 |            -15.6 |                26.47 |                 34.81 |
| 5 stocks, quarterly, keep top 5, trend filter, 6-1m momentum  |      25.3  |     0.97 |              -41.2 |            -23   |                19.69 |                 25.89 |
| 5 stocks, monthly, keep top 10, trend filter, 12-1m momentum  |      25.66 |     0.97 |              -34.2 |             -9.5 |                11.94 |                 15.7  |
