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
| S&P 500 ETF, buy and hold                  |      11.4  |                 8.87 |               13.82 |     0.78 |              -18.7 |            -13.9 |
| Same 38 stocks, equal weight, buy and hold |      21.38 |                17.64 |               25.06 |     1.05 |              -35.5 |            -15.1 |

## Starting with 10,000 kr (sorted by Sharpe)

| name                                                          |   cagr_pct |   cagr_2012_2018_pct |   cagr_2019_now_pct |   sharpe |   max_drawdown_pct |   worst_year_pct |   costs_pct_per_year |   turnover_x_per_year |
|:--------------------------------------------------------------|-----------:|---------------------:|--------------------:|---------:|-------------------:|-----------------:|---------------------:|----------------------:|
| 3 stocks, monthly, keep top 6, trend filter, 6-1m momentum    |      32.75 |                36.51 |               30.18 |     1.08 |              -42.8 |            -29.1 |                 2.72 |                  3.57 |
| 3 stocks, quarterly, keep top 3, trend filter, 6-1m momentum  |      31.37 |                30.44 |               32.64 |     1.05 |              -43.1 |            -25.5 |                 2.08 |                  2.73 |
| Same 38 stocks, equal weight, buy and hold                    |      21.38 |                17.64 |               25.06 |     1.05 |              -35.5 |            -15.1 |                 0.05 |                  0.03 |
| 4 stocks, quarterly, keep top 8, no filter, 12-1m momentum    |      27.93 |                21.72 |               33.61 |     1.05 |              -33.3 |             -9.9 |                 0.87 |                  1.13 |
| 3 stocks, quarterly, keep top 3, no filter, 6-1m momentum     |      31.08 |                29.38 |               33.06 |     1.04 |              -43   |            -25.4 |                 2.09 |                  2.75 |
| 5 stocks, quarterly, keep top 10, no filter, 12-1m momentum   |      26.86 |                18.58 |               34.65 |     1.03 |              -33.5 |             -6.1 |                 0.7  |                  0.9  |
| 3 stocks, monthly, keep top 6, no filter, 6-1m momentum       |      30.67 |                32.02 |               30.13 |     1.03 |              -44.2 |            -31.7 |                 2.7  |                  3.54 |
| 5 stocks, monthly, keep top 10, NO COSTS (reference)          |      27.42 |                24.93 |               29.74 |     1.03 |              -35.1 |            -10.7 |                 0    |                  1.59 |
| 8 stocks, monthly, keep top 8, trend filter, 6-1m momentum    |      24.89 |                22.45 |               27.64 |     1.03 |              -38.4 |            -15.5 |                 3.34 |                  4.16 |
| 6 stocks, quarterly, keep top 12, no filter, 12-1m momentum   |      25.58 |                17.43 |               33.22 |     1.02 |              -31.5 |             -7.1 |                 0.64 |                  0.8  |
| 8 stocks, monthly, keep top 16, no filter, 6-1m momentum      |      25.03 |                23.27 |               27.14 |     1.02 |              -37   |            -12.6 |                 1.89 |                  2.36 |
| 4 stocks, monthly, keep top 8, trend filter, 6-1m momentum    |      28.36 |                33.21 |               24.77 |     1.02 |              -37   |            -18.9 |                 2.66 |                  3.48 |
| 5 stocks, quarterly, keep top 5, no filter, 6-1m momentum     |      26.72 |                23.82 |               29.79 |     1.02 |              -39.8 |            -22.4 |                 2    |                  2.59 |
| 3 stocks, quarterly, keep top 3, no filter, 12-1m momentum    |      30.21 |                24.76 |               35.09 |     1.01 |              -36.6 |             -7.3 |                 1.27 |                  1.66 |
| 4 stocks, monthly, keep top 8, no filter, 6-1m momentum       |      27.83 |                29    |               27.37 |     1.01 |              -37   |            -19.8 |                 2.58 |                  3.37 |
| 6 stocks, quarterly, keep top 12, no filter, 6-1m momentum    |      25.42 |                20.56 |               29.97 |     1.01 |              -34.7 |            -20   |                 1.31 |                  1.65 |
| 6 stocks, quarterly, keep top 6, no filter, 6-1m momentum     |      24.95 |                23.37 |               26.73 |     1.01 |              -37.6 |            -15   |                 1.97 |                  2.52 |
| 3 stocks, monthly, keep top 3, trend filter, 6-1m momentum    |      29.74 |                35.22 |               25.61 |     1    |              -43.8 |            -19.8 |                 4.22 |                  5.54 |
| 3 stocks, quarterly, keep top 6, no filter, 6-1m momentum     |      28.38 |                22.23 |               34.36 |     1    |              -43   |            -24.9 |                 1.61 |                  2.11 |
| 5 stocks, quarterly, keep top 5, trend filter, 6-1m momentum  |      25.81 |                24.17 |               27.71 |     1    |              -40   |            -22.3 |                 1.99 |                  2.57 |
| 8 stocks, monthly, keep top 8, no filter, 6-1m momentum       |      24.15 |                22.01 |               26.53 |     1    |              -38.9 |            -14.9 |                 3.45 |                  4.28 |
| 5 stocks, monthly, keep top 10, no filter, 12-1m momentum     |      26.51 |                20.39 |               32.22 |     0.99 |              -32.4 |            -12.2 |                 1.08 |                  1.38 |
| 4 stocks, monthly, keep top 8, no filter, 12-1m momentum      |      28.67 |                24.54 |               32.41 |     0.99 |              -33.6 |             -6.7 |                 1.23 |                  1.61 |
| 6 stocks, monthly, keep top 6, no filter, 12-1m momentum      |      25.63 |                23.05 |               28.15 |     0.99 |              -34.5 |              0.2 |                 2.35 |                  2.99 |
| 5 stocks, monthly, keep top 10, trend filter, 12-1m momentum  |      25.75 |                23.06 |               28.26 |     0.99 |              -35.6 |            -11.4 |                 1.23 |                  1.58 |
| 4 stocks, quarterly, keep top 8, trend filter, 12-1m momentum |      26.06 |                22.87 |               28.86 |     0.99 |              -35.1 |             -2.4 |                 0.92 |                  1.19 |
| 4 stocks, monthly, keep top 4, no filter, 6-1m momentum       |      27.87 |                29.66 |               27.13 |     0.99 |              -41   |            -22.8 |                 3.9  |                  5.1  |
| 6 stocks, quarterly, keep top 6, no filter, 12-1m momentum    |      24.28 |                19.65 |               28.53 |     0.99 |              -30.3 |              0.9 |                 1.31 |                  1.65 |
| 6 stocks, quarterly, keep top 6, trend filter, 6-1m momentum  |      24.42 |                22.83 |               26.16 |     0.99 |              -37.8 |            -15.3 |                 1.89 |                  2.41 |
| 3 stocks, monthly, keep top 3, no filter, 6-1m momentum       |      29.23 |                34.22 |               25.5  |     0.98 |              -43.8 |            -19.8 |                 4.32 |                  5.68 |

## Baselines, 100,000 kr

| name                                       |   cagr_pct |   cagr_2012_2018_pct |   cagr_2019_now_pct |   sharpe |   max_drawdown_pct |   worst_year_pct |
|:-------------------------------------------|-----------:|---------------------:|--------------------:|---------:|-------------------:|-----------------:|
| S&P 500 ETF, buy and hold                  |      11.4  |                 8.87 |               13.82 |     0.78 |              -18.7 |            -13.9 |
| Same 38 stocks, equal weight, buy and hold |      18.88 |                18.45 |               19.42 |     0.98 |              -30.6 |            -21.1 |

## Starting with 100,000 kr (sorted by Sharpe)

| name                                                         |   cagr_pct |   cagr_2012_2018_pct |   cagr_2019_now_pct |   sharpe |   max_drawdown_pct |   worst_year_pct |   costs_pct_per_year |   turnover_x_per_year |
|:-------------------------------------------------------------|-----------:|---------------------:|--------------------:|---------:|-------------------:|-----------------:|---------------------:|----------------------:|
| 3 stocks, monthly, keep top 6, trend filter, 6-1m momentum   |      32.76 |                36.83 |               29.92 |     1.08 |              -42.7 |            -29.1 |                 2.72 |                  3.58 |
| 3 stocks, quarterly, keep top 3, trend filter, 6-1m momentum |      31.66 |                30.88 |               32.8  |     1.05 |              -43.2 |            -25.6 |                 2.09 |                  2.75 |
| 3 stocks, quarterly, keep top 3, no filter, 6-1m momentum    |      31.34 |                29.77 |               33.2  |     1.05 |              -43.2 |            -25.6 |                 2.1  |                  2.76 |
| 3 stocks, monthly, keep top 6, no filter, 6-1m momentum      |      30.69 |                32.67 |               29.63 |     1.03 |              -44.5 |            -32   |                 2.74 |                  3.6  |
| 4 stocks, quarterly, keep top 8, no filter, 12-1m momentum   |      27.27 |                20.16 |               33.84 |     1.03 |              -33.5 |             -9.9 |                 0.87 |                  1.15 |
| 4 stocks, monthly, keep top 8, trend filter, 6-1m momentum   |      28.58 |                33.81 |               24.67 |     1.03 |              -37.3 |            -19.2 |                 2.67 |                  3.51 |
| 4 stocks, monthly, keep top 8, no filter, 6-1m momentum      |      28.89 |                31.65 |               27.02 |     1.03 |              -37.3 |            -19.7 |                 2.62 |                  3.44 |
| 5 stocks, monthly, keep top 10, NO COSTS (reference)         |      27.71 |                24.99 |               30.27 |     1.03 |              -35.3 |            -10.4 |                 0    |                  1.6  |
| 5 stocks, quarterly, keep top 5, no filter, 6-1m momentum    |      27.06 |                24.27 |               30.05 |     1.02 |              -41.1 |            -22.5 |                 1.98 |                  2.6  |
| 5 stocks, quarterly, keep top 10, no filter, 12-1m momentum  |      26.63 |                19.07 |               33.7  |     1.02 |              -33.7 |             -6.5 |                 0.69 |                  0.91 |
| 6 stocks, quarterly, keep top 12, no filter, 12-1m momentum  |      25.56 |                18.18 |               32.43 |     1.01 |              -32.5 |             -7.1 |                 0.61 |                  0.81 |
| 8 stocks, quarterly, keep top 16, no filter, 12-1m momentum  |      22.93 |                19.38 |               26.13 |     1.01 |              -28.5 |             -7.6 |                 0.59 |                  0.78 |
| 6 stocks, quarterly, keep top 6, no filter, 6-1m momentum    |      25.44 |                24.09 |               27    |     1.01 |              -39   |            -15.9 |                 1.93 |                  2.54 |
| 3 stocks, quarterly, keep top 6, no filter, 6-1m momentum    |      28.48 |                22.78 |               34.06 |     1    |              -43.2 |            -24.8 |                 1.63 |                  2.15 |
| 3 stocks, monthly, keep top 3, trend filter, 6-1m momentum   |      29.88 |                35.33 |               25.77 |     1    |              -44   |            -19.8 |                 4.23 |                  5.57 |
| 6 stocks, quarterly, keep top 6, trend filter, 6-1m momentum |      25.05 |                24.2  |               26.15 |     1    |              -38.9 |            -15.9 |                 1.86 |                  2.45 |
| 6 stocks, quarterly, keep top 12, no filter, 6-1m momentum   |      25.55 |                21.07 |               29.75 |     1    |              -35.8 |            -20.2 |                 1.28 |                  1.68 |
| 5 stocks, monthly, keep top 10, trend filter, 12-1m momentum |      26.39 |                23.54 |               29.05 |     1    |              -35.6 |            -11.5 |                 1.23 |                  1.62 |
| 5 stocks, quarterly, keep top 5, trend filter, 6-1m momentum |      26.07 |                24.56 |               27.88 |     0.99 |              -41.2 |            -22.5 |                 1.97 |                  2.59 |
| 8 stocks, monthly, keep top 8, trend filter, 6-1m momentum   |      23.3  |                24.72 |               22.64 |     0.99 |              -33.8 |            -15.6 |                 3.22 |                  4.23 |
| 6 stocks, monthly, keep top 6, no filter, 12-1m momentum     |      25.6  |                23.32 |               27.81 |     0.99 |              -34.8 |             -0.1 |                 2.32 |                  3.06 |
| 4 stocks, quarterly, keep top 4, no filter, 6-1m momentum    |      27.04 |                23.57 |               30.48 |     0.99 |              -41.6 |            -26   |                 2.11 |                  2.78 |
| 8 stocks, monthly, keep top 16, no filter, 12-1m momentum    |      24.21 |                19.33 |               28.68 |     0.99 |              -32.9 |            -12.2 |                 0.73 |                  0.96 |
| 4 stocks, monthly, keep top 8, no filter, 12-1m momentum     |      28.84 |                24.67 |               32.62 |     0.99 |              -34.1 |             -6.7 |                 1.23 |                  1.62 |
| 4 stocks, monthly, keep top 4, no filter, 6-1m momentum      |      28.01 |                29.85 |               27.25 |     0.99 |              -40.9 |            -23.1 |                 3.91 |                  5.14 |
| 4 stocks, monthly, keep top 4, trend filter, 6-1m momentum   |      27.81 |                31.22 |               25.7  |     0.99 |              -40.9 |            -24.5 |                 3.81 |                  5.02 |
| 8 stocks, quarterly, keep top 8, no filter, 12-1m momentum   |      23.35 |                17.1  |               29.13 |     0.98 |              -30.4 |             -3.1 |                 1.08 |                  1.41 |
| 6 stocks, monthly, keep top 12, trend filter, 6-1m momentum  |      24.52 |                26.78 |               23.26 |     0.98 |              -34.9 |            -15.4 |                 2.23 |                  2.93 |
| 6 stocks, monthly, keep top 12, no filter, 6-1m momentum     |      24.62 |                26.44 |               23.74 |     0.98 |              -35.3 |            -16   |                 2.14 |                  2.82 |
| 3 stocks, monthly, keep top 3, no filter, 6-1m momentum      |      29.44 |                34.53 |               25.62 |     0.98 |              -44   |            -19.8 |                 4.33 |                  5.7  |
