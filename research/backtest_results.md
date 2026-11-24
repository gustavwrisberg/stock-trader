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

## Baselines, 10,000 kr

| name                                       |   cagr_pct |   cagr_2012_2018_pct |   cagr_2019_now_pct |   sharpe |   max_drawdown_pct |   worst_year_pct |
|:-------------------------------------------|-----------:|---------------------:|--------------------:|---------:|-------------------:|-----------------:|
| S&P 500 ETF, buy and hold                  |      13.22 |                12.07 |               14.27 |     0.77 |              -33.1 |            -17.4 |
| Same 38 stocks, equal weight, buy and hold |      22.52 |                18.09 |               26.78 |     0.97 |              -36.5 |            -32.2 |

## Starting with 10,000 kr (sorted by Sharpe)

| name                                                          |   cagr_pct |   cagr_2012_2018_pct |   cagr_2019_now_pct |   sharpe |   max_drawdown_pct |   worst_year_pct |   costs_pct_per_year |   turnover_x_per_year |
|:--------------------------------------------------------------|-----------:|---------------------:|--------------------:|---------:|-------------------:|-----------------:|---------------------:|----------------------:|
| 3 stocks, monthly, keep top 6, trend filter, 6-1m momentum    |      37.37 |                41.73 |               34.39 |     1.12 |              -46.6 |            -31.7 |                 2.61 |                  3.43 |
| 4 stocks, monthly, keep top 8, no filter, 6-1m momentum       |      33.11 |                36    |               31.22 |     1.07 |              -43.5 |            -19.2 |                 2.48 |                  3.25 |
| 3 stocks, monthly, keep top 6, no filter, 6-1m momentum       |      34.26 |                36.57 |               33.04 |     1.06 |              -47.4 |            -35.6 |                 2.58 |                  3.39 |
| 4 stocks, monthly, keep top 8, trend filter, 6-1m momentum    |      31.29 |                33.34 |               30.37 |     1.04 |              -44   |            -18.5 |                 2.54 |                  3.33 |
| 5 stocks, monthly, keep top 10, no filter, 6-1m momentum      |      30.23 |                33.03 |               28.62 |     1.04 |              -41.3 |            -16.2 |                 2.3  |                  3    |
| 3 stocks, quarterly, keep top 3, no filter, 6-1m momentum     |      32.79 |                34.08 |               32.18 |     1.03 |              -43.1 |            -28.4 |                 2.06 |                  2.7  |
| 3 stocks, quarterly, keep top 3, trend filter, 6-1m momentum  |      32.38 |                33.91 |               31.58 |     1.02 |              -43   |            -28.4 |                 2.07 |                  2.71 |
| 4 stocks, monthly, keep top 4, no filter, 6-1m momentum       |      30.51 |                32.49 |               29.65 |     1.02 |              -45   |            -22.8 |                 3.88 |                  5.08 |
| 3 stocks, monthly, keep top 3, no filter, 6-1m momentum       |      32.97 |                37.11 |               30.05 |     1.02 |              -49   |            -23.8 |                 4.2  |                  5.52 |
| 3 stocks, monthly, keep top 3, trend filter, 6-1m momentum    |      32.4  |                35.88 |               30.04 |     1.02 |              -49.1 |            -23.7 |                 4.09 |                  5.37 |
| 5 stocks, monthly, keep top 10, NO COSTS (reference)          |      29.15 |                29.69 |               28.79 |     1.02 |              -37   |            -18.8 |                 0    |                  1.5  |
| 3 stocks, quarterly, keep top 3, no filter, 12-1m momentum    |      31.44 |                33.01 |               30.82 |     1.01 |              -36.7 |             -9.4 |                 1.17 |                  1.53 |
| 4 stocks, monthly, keep top 4, trend filter, 6-1m momentum    |      29.75 |                31.65 |               28.95 |     1    |              -45.2 |            -24.3 |                 3.73 |                  4.87 |
| 4 stocks, monthly, keep top 8, no filter, 12-1m momentum      |      30.65 |                31.02 |               30.69 |     1    |              -34.1 |             -6   |                 1.09 |                  1.42 |
| 6 stocks, monthly, keep top 12, no filter, 6-1m momentum      |      26.71 |                28.83 |               25.64 |     1    |              -38.5 |            -18.6 |                 2.11 |                  2.72 |
| 3 stocks, quarterly, keep top 3, trend filter, 12-1m momentum |      30.63 |                34.07 |               28.39 |     0.99 |              -36.5 |             -7   |                 1.13 |                  1.47 |
| 4 stocks, monthly, keep top 4, no filter, 12-1m momentum      |      29.94 |                32.77 |               27.9  |     0.99 |              -39   |            -11.6 |                 2.4  |                  3.13 |
| 8 stocks, monthly, keep top 8, trend filter, 6-1m momentum    |      24.12 |                25.39 |               23.69 |     0.99 |              -37.4 |            -15.4 |                 3.26 |                  4.06 |
| 5 stocks, monthly, keep top 10, trend filter, 6-1m momentum   |      28    |                30.22 |               26.92 |     0.99 |              -42.9 |            -19.2 |                 2.36 |                  3.07 |
| 6 stocks, quarterly, keep top 6, no filter, 6-1m momentum     |      25.69 |                28.84 |               23.54 |     0.98 |              -38.5 |            -22.8 |                 1.9  |                  2.43 |
| 6 stocks, monthly, keep top 12, trend filter, 6-1m momentum   |      26.36 |                27.18 |               26.41 |     0.98 |              -40.3 |            -18.4 |                 2.2  |                  2.83 |
| 3 stocks, quarterly, keep top 6, no filter, 6-1m momentum     |      29.91 |                28.16 |               32.21 |     0.98 |              -43   |            -25.3 |                 1.54 |                  2.01 |
| 4 stocks, quarterly, keep top 8, no filter, 12-1m momentum    |      28.6  |                24.13 |               32.55 |     0.98 |              -42.2 |            -10   |                 0.79 |                  1.03 |
| 6 stocks, monthly, keep top 6, no filter, 12-1m momentum      |      26.79 |                26.24 |               27.54 |     0.98 |              -35.4 |             -5.2 |                 2.14 |                  2.73 |
| 5 stocks, monthly, keep top 5, trend filter, 6-1m momentum    |      27.06 |                30.04 |               25.24 |     0.98 |              -43.7 |            -26.8 |                 3.56 |                  4.63 |
| 8 stocks, monthly, keep top 16, no filter, 6-1m momentum      |      24.55 |                24.5  |               25.26 |     0.98 |              -38.1 |            -15   |                 1.78 |                  2.22 |
| 8 stocks, monthly, keep top 16, trend filter, 6-1m momentum   |      23.6  |                26.32 |               21.9  |     0.98 |              -36.8 |            -15.5 |                 1.78 |                  2.22 |
| 4 stocks, monthly, keep top 4, trend filter, 12-1m momentum   |      28.95 |                33.4  |               25.46 |     0.98 |              -39.1 |            -22   |                 2.41 |                  3.14 |
| 3 stocks, monthly, keep top 3, trend filter, 12-1m momentum   |      30.41 |                38.34 |               24.19 |     0.98 |              -42.1 |            -22.3 |                 2.83 |                  3.71 |
| 5 stocks, monthly, keep top 10, trend filter, 12-1m momentum  |      27.47 |                27.85 |               27.21 |     0.97 |              -37.4 |            -18   |                 1.17 |                  1.5  |

## Baselines, 100,000 kr

| name                                       |   cagr_pct |   cagr_2012_2018_pct |   cagr_2019_now_pct |   sharpe |   max_drawdown_pct |   worst_year_pct |
|:-------------------------------------------|-----------:|---------------------:|--------------------:|---------:|-------------------:|-----------------:|
| S&P 500 ETF, buy and hold                  |      13.23 |                12.09 |               14.28 |     0.77 |              -33.1 |            -17.4 |
| Same 38 stocks, equal weight, buy and hold |      21.31 |                19.91 |               22.76 |     1    |              -31   |            -25.3 |

## Starting with 100,000 kr (sorted by Sharpe)

| name                                                          |   cagr_pct |   cagr_2012_2018_pct |   cagr_2019_now_pct |   sharpe |   max_drawdown_pct |   worst_year_pct |   costs_pct_per_year |   turnover_x_per_year |
|:--------------------------------------------------------------|-----------:|---------------------:|--------------------:|---------:|-------------------:|-----------------:|---------------------:|----------------------:|
| 3 stocks, monthly, keep top 6, trend filter, 6-1m momentum    |      37.53 |                42.16 |               34.33 |     1.12 |              -46.5 |            -31.7 |                 2.61 |                  3.44 |
| 4 stocks, monthly, keep top 8, no filter, 6-1m momentum       |      33.3  |                36.58 |               31.09 |     1.08 |              -43.2 |            -19.3 |                 2.48 |                  3.26 |
| 3 stocks, monthly, keep top 6, no filter, 6-1m momentum       |      34.4  |                36.84 |               33.07 |     1.06 |              -47.4 |            -35.6 |                 2.59 |                  3.4  |
| 5 stocks, monthly, keep top 10, no filter, 6-1m momentum      |      30.45 |                33.95 |               28.26 |     1.05 |              -41   |            -16   |                 2.28 |                  3    |
| 4 stocks, monthly, keep top 8, trend filter, 6-1m momentum    |      31.1  |                33.56 |               29.84 |     1.04 |              -43.2 |            -18.5 |                 2.54 |                  3.34 |
| 3 stocks, quarterly, keep top 3, no filter, 6-1m momentum     |      32.89 |                34.24 |               32.25 |     1.03 |              -43.2 |            -28.4 |                 2.08 |                  2.74 |
| 3 stocks, monthly, keep top 3, no filter, 6-1m momentum       |      33.16 |                37.51 |               30.06 |     1.03 |              -49.1 |            -23.8 |                 4.21 |                  5.54 |
| 3 stocks, quarterly, keep top 3, trend filter, 6-1m momentum  |      32.68 |                34.34 |               31.77 |     1.03 |              -43.2 |            -28.4 |                 2.05 |                  2.7  |
| 4 stocks, monthly, keep top 4, trend filter, 6-1m momentum    |      30.3  |                33.17 |               28.69 |     1.02 |              -44.9 |            -24.4 |                 3.73 |                  4.9  |
| 3 stocks, monthly, keep top 3, trend filter, 6-1m momentum    |      32.45 |                36    |               30.02 |     1.02 |              -49.1 |            -23.9 |                 4.1  |                  5.39 |
| 3 stocks, quarterly, keep top 3, no filter, 12-1m momentum    |      31.71 |                33.33 |               31.03 |     1.01 |              -36.8 |             -9.2 |                 1.17 |                  1.54 |
| 6 stocks, monthly, keep top 12, no filter, 6-1m momentum      |      26.95 |                29.8  |               25.24 |     1.01 |              -38.4 |            -19   |                 2.08 |                  2.74 |
| 4 stocks, monthly, keep top 4, no filter, 6-1m momentum       |      30.46 |                32.46 |               29.58 |     1.01 |              -44.8 |            -22.9 |                 3.88 |                  5.1  |
| 4 stocks, monthly, keep top 8, no filter, 12-1m momentum      |      30.59 |                31.03 |               30.56 |     1    |              -34.1 |             -6   |                 1.08 |                  1.43 |
| 5 stocks, monthly, keep top 10, trend filter, 6-1m momentum   |      28.4  |                30.67 |               27.3  |     1    |              -43.2 |            -19.1 |                 2.35 |                  3.09 |
| Same 38 stocks, equal weight, buy and hold                    |      21.31 |                19.91 |               22.76 |     1    |              -31   |            -25.3 |                 0.02 |                  0.02 |
| 3 stocks, quarterly, keep top 3, trend filter, 12-1m momentum |      30.85 |                34.38 |               28.53 |     1    |              -36.8 |             -6.9 |                 1.12 |                  1.48 |
| 8 stocks, monthly, keep top 16, no filter, 6-1m momentum      |      25.31 |                26.08 |               25.31 |     1    |              -38.4 |            -15.4 |                 1.7  |                  2.24 |
| 8 stocks, monthly, keep top 8, trend filter, 6-1m momentum    |      24.62 |                27.28 |               23    |     1    |              -36.3 |            -15.6 |                 3.15 |                  4.14 |
| 5 stocks, monthly, keep top 10, NO COSTS (reference)          |      28.61 |                28.59 |               28.7  |     1    |              -37   |            -18.5 |                 0    |                  1.53 |
| 4 stocks, monthly, keep top 4, no filter, 12-1m momentum      |      29.9  |                33.08 |               27.57 |     0.99 |              -38.9 |            -11.6 |                 2.4  |                  3.16 |
| 5 stocks, monthly, keep top 5, trend filter, 6-1m momentum    |      27.56 |                30.78 |               25.58 |     0.99 |              -43.9 |            -26.9 |                 3.55 |                  4.66 |
| 8 stocks, monthly, keep top 16, trend filter, 6-1m momentum   |      24.69 |                27.14 |               23.23 |     0.99 |              -38.2 |            -15.7 |                 1.71 |                  2.24 |
| 6 stocks, quarterly, keep top 6, no filter, 6-1m momentum     |      26.04 |                29.38 |               23.74 |     0.98 |              -39   |            -24.7 |                 1.85 |                  2.44 |
| 3 stocks, quarterly, keep top 6, no filter, 6-1m momentum     |      30.07 |                28.42 |               32.28 |     0.98 |              -43.2 |            -25.5 |                 1.54 |                  2.03 |
| 6 stocks, monthly, keep top 6, no filter, 12-1m momentum      |      26.97 |                26.82 |               27.42 |     0.98 |              -35.3 |             -5.2 |                 2.09 |                  2.75 |
| 4 stocks, monthly, keep top 4, trend filter, 12-1m momentum   |      28.98 |                33.91 |               25.1  |     0.98 |              -39.3 |            -23.3 |                 2.41 |                  3.17 |
| 3 stocks, monthly, keep top 3, trend filter, 12-1m momentum   |      30.43 |                38.61 |               24.01 |     0.98 |              -42.2 |            -22.6 |                 2.84 |                  3.74 |
| 4 stocks, quarterly, keep top 4, no filter, 6-1m momentum     |      28.61 |                29.23 |               28.48 |     0.98 |              -41.6 |            -27.9 |                 2.07 |                  2.72 |
| 5 stocks, monthly, keep top 10, trend filter, 12-1m momentum  |      27.21 |                27.21 |               27.27 |     0.97 |              -37.4 |            -20.3 |                 1.16 |                  1.52 |
