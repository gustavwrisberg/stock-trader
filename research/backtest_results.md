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

Period 2012-01-03 to 2026-11-24, values in DKK after Saxo costs and 17% ASK tax.
value_of_80k_after_10y_real_kr: 80,000 kr put in 10 years before the end, in start-month kroner after Danish inflation (Statistics Denmark PRIS01).

## Baselines, 10,000 kr

| name                                       |   cagr_pct |   cagr_2012_2018_pct |   cagr_2019_now_pct |   sharpe |   max_drawdown_pct |   worst_year_pct |
|:-------------------------------------------|-----------:|---------------------:|--------------------:|---------:|-------------------:|-----------------:|
| S&P 500 ETF, buy and hold                  |      13.18 |                12.07 |               14.19 |     0.77 |              -33.1 |            -17.4 |
| Same 38 stocks, equal weight, buy and hold |      22.39 |                18.09 |               26.52 |     0.97 |              -36.5 |            -32.2 |

## Starting with 10,000 kr (sorted by Sharpe)

| name                                                          |   cagr_pct |   cagr_2012_2018_pct |   cagr_2019_now_pct |   sharpe |   max_drawdown_pct |   worst_year_pct |   costs_pct_per_year |   turnover_x_per_year |   value_of_80k_after_10y_real_kr |
|:--------------------------------------------------------------|-----------:|---------------------:|--------------------:|---------:|-------------------:|-----------------:|---------------------:|----------------------:|---------------------------------:|
| 3 stocks, monthly, keep top 6, trend filter, 6-1m momentum    |      37.55 |                41.73 |               34.72 |     1.13 |              -46.6 |            -31.7 |                 2.61 |                  3.42 |                           999050 |
| 4 stocks, monthly, keep top 8, no filter, 6-1m momentum       |      33.22 |                36    |               31.42 |     1.08 |              -43.5 |            -19.2 |                 2.48 |                  3.24 |                           813037 |
| 3 stocks, monthly, keep top 6, no filter, 6-1m momentum       |      34.29 |                36.57 |               33.09 |     1.06 |              -47.4 |            -35.6 |                 2.58 |                  3.39 |                           912033 |
| 5 stocks, monthly, keep top 10, no filter, 6-1m momentum      |      30.35 |                33.03 |               28.84 |     1.05 |              -41.3 |            -16.2 |                 2.3  |                  2.99 |                           689252 |
| 4 stocks, monthly, keep top 8, trend filter, 6-1m momentum    |      31.5  |                33.34 |               30.78 |     1.04 |              -44   |            -18.5 |                 2.54 |                  3.32 |                           762814 |
| 3 stocks, quarterly, keep top 3, no filter, 6-1m momentum     |      32.96 |                34.08 |               32.5  |     1.03 |              -43.1 |            -28.4 |                 2.06 |                  2.7  |                           866256 |
| 3 stocks, monthly, keep top 3, no filter, 6-1m momentum       |      33.11 |                37.11 |               30.32 |     1.03 |              -49   |            -23.8 |                 4.2  |                  5.52 |                           703244 |
| 4 stocks, monthly, keep top 4, no filter, 6-1m momentum       |      30.63 |                32.49 |               29.88 |     1.02 |              -45   |            -22.8 |                 3.88 |                  5.08 |                           707823 |
| 3 stocks, quarterly, keep top 3, trend filter, 6-1m momentum  |      32.55 |                33.91 |               31.9  |     1.02 |              -43   |            -28.4 |                 2.07 |                  2.71 |                           833118 |
| 3 stocks, monthly, keep top 3, trend filter, 6-1m momentum    |      32.65 |                35.88 |               30.52 |     1.02 |              -49.1 |            -23.7 |                 4.09 |                  5.37 |                           717309 |
| 5 stocks, monthly, keep top 10, NO COSTS (reference)          |      29.27 |                29.69 |               29.02 |     1.02 |              -37   |            -18.8 |                 0    |                  1.5  |                           651012 |
| 4 stocks, monthly, keep top 4, trend filter, 6-1m momentum    |      29.97 |                31.65 |               29.35 |     1.01 |              -45.2 |            -24.3 |                 3.72 |                  4.87 |                           680712 |
| 3 stocks, quarterly, keep top 3, no filter, 12-1m momentum    |      31.26 |                33.01 |               30.48 |     1.01 |              -36.7 |            -11.2 |                 1.17 |                  1.52 |                           887554 |
| 4 stocks, monthly, keep top 8, no filter, 12-1m momentum      |      30.4  |                31.02 |               30.22 |     1    |              -34.1 |             -8.6 |                 1.09 |                  1.41 |                           725796 |
| 6 stocks, monthly, keep top 12, no filter, 6-1m momentum      |      26.76 |                28.83 |               25.74 |     1    |              -38.5 |            -18.6 |                 2.11 |                  2.72 |                           556007 |
| 4 stocks, monthly, keep top 4, trend filter, 12-1m momentum   |      29.07 |                33.4  |               25.68 |     0.99 |              -39.1 |            -22   |                 2.41 |                  3.14 |                           539332 |
| 3 stocks, quarterly, keep top 3, trend filter, 12-1m momentum |      30.45 |                34.07 |               28.05 |     0.99 |              -36.5 |             -8.9 |                 1.13 |                  1.47 |                           765906 |
| 8 stocks, monthly, keep top 8, trend filter, 6-1m momentum    |      24.3  |                25.39 |               24.02 |     0.99 |              -37.4 |            -15.4 |                 3.26 |                  4.05 |                           511428 |
| 5 stocks, monthly, keep top 10, trend filter, 6-1m momentum   |      28.22 |                30.22 |               27.34 |     0.99 |              -42.9 |            -19.2 |                 2.36 |                  3.07 |                           615357 |
| 6 stocks, monthly, keep top 12, trend filter, 6-1m momentum   |      26.58 |                27.18 |               26.82 |     0.99 |              -40.3 |            -18.4 |                 2.2  |                  2.83 |                           583177 |
| 4 stocks, monthly, keep top 4, no filter, 12-1m momentum      |      29.77 |                32.77 |               27.58 |     0.99 |              -39   |            -11.6 |                 2.4  |                  3.13 |                           601518 |
| 5 stocks, monthly, keep top 5, trend filter, 6-1m momentum    |      27.28 |                30.04 |               25.65 |     0.99 |              -43.7 |            -26.8 |                 3.56 |                  4.63 |                           520953 |
| 6 stocks, monthly, keep top 6, no filter, 12-1m momentum      |      26.71 |                26.24 |               27.4  |     0.98 |              -35.4 |             -5.2 |                 2.14 |                  2.73 |                           569898 |
| 6 stocks, quarterly, keep top 6, no filter, 6-1m momentum     |      25.82 |                28.84 |               23.79 |     0.98 |              -38.5 |            -22.8 |                 1.9  |                  2.42 |                           538330 |
| 5 stocks, monthly, keep top 10, trend filter, 12-1m momentum  |      27.59 |                27.85 |               27.42 |     0.98 |              -37.4 |            -18   |                 1.17 |                  1.5  |                           575536 |
| 4 stocks, quarterly, keep top 4, no filter, 6-1m momentum     |      28.41 |                28.72 |               28.54 |     0.98 |              -41.5 |            -27.8 |                 2.05 |                  2.67 |                           632174 |
| 8 stocks, monthly, keep top 16, trend filter, 6-1m momentum   |      23.75 |                26.32 |               22.19 |     0.98 |              -36.8 |            -15.5 |                 1.78 |                  2.22 |                           443913 |
| 3 stocks, quarterly, keep top 6, no filter, 6-1m momentum     |      30.01 |                28.16 |               32.39 |     0.98 |              -43   |            -25.3 |                 1.54 |                  2.01 |                           956152 |
| 3 stocks, monthly, keep top 3, trend filter, 12-1m momentum   |      30.46 |                38.34 |               24.28 |     0.98 |              -42.1 |            -22.3 |                 2.83 |                  3.71 |                           493250 |
| 8 stocks, monthly, keep top 16, no filter, 6-1m momentum      |      24.54 |                24.5  |               25.24 |     0.98 |              -38.1 |            -15   |                 1.78 |                  2.22 |                           508406 |

## Baselines, 100,000 kr

| name                                       |   cagr_pct |   cagr_2012_2018_pct |   cagr_2019_now_pct |   sharpe |   max_drawdown_pct |   worst_year_pct |
|:-------------------------------------------|-----------:|---------------------:|--------------------:|---------:|-------------------:|-----------------:|
| S&P 500 ETF, buy and hold                  |      13.2  |                12.09 |               14.21 |     0.77 |              -33.1 |            -17.4 |
| Same 38 stocks, equal weight, buy and hold |      21.23 |                19.91 |               22.62 |     1    |              -31   |            -25.3 |

## Starting with 100,000 kr (sorted by Sharpe)

| name                                                          |   cagr_pct |   cagr_2012_2018_pct |   cagr_2019_now_pct |   sharpe |   max_drawdown_pct |   worst_year_pct |   costs_pct_per_year |   turnover_x_per_year |   value_of_80k_after_10y_real_kr |
|:--------------------------------------------------------------|-----------:|---------------------:|--------------------:|---------:|-------------------:|-----------------:|---------------------:|----------------------:|---------------------------------:|
| 3 stocks, monthly, keep top 6, trend filter, 6-1m momentum    |      37.71 |                42.16 |               34.66 |     1.13 |              -46.5 |            -31.7 |                 2.61 |                  3.43 |                           996745 |
| 4 stocks, monthly, keep top 8, no filter, 6-1m momentum       |      33.41 |                36.58 |               31.29 |     1.08 |              -43.2 |            -19.3 |                 2.48 |                  3.26 |                           813051 |
| 3 stocks, monthly, keep top 6, no filter, 6-1m momentum       |      34.43 |                36.84 |               33.12 |     1.06 |              -47.4 |            -35.6 |                 2.58 |                  3.4  |                           914484 |
| 5 stocks, monthly, keep top 10, no filter, 6-1m momentum      |      30.56 |                33.95 |               28.46 |     1.05 |              -41   |            -16   |                 2.28 |                  3    |                           676780 |
| 4 stocks, monthly, keep top 8, trend filter, 6-1m momentum    |      31.32 |                33.56 |               30.25 |     1.04 |              -43.2 |            -18.5 |                 2.54 |                  3.34 |                           741899 |
| 3 stocks, quarterly, keep top 3, no filter, 6-1m momentum     |      33.06 |                34.24 |               32.57 |     1.03 |              -43.2 |            -28.4 |                 2.08 |                  2.74 |                           869944 |
| 3 stocks, monthly, keep top 3, no filter, 6-1m momentum       |      33.3  |                37.51 |               30.33 |     1.03 |              -49.1 |            -23.8 |                 4.21 |                  5.53 |                           701889 |
| 3 stocks, quarterly, keep top 3, trend filter, 6-1m momentum  |      32.85 |                34.34 |               32.09 |     1.03 |              -43.2 |            -28.4 |                 2.05 |                  2.69 |                           845770 |
| 4 stocks, monthly, keep top 4, trend filter, 6-1m momentum    |      30.52 |                33.17 |               29.09 |     1.02 |              -44.9 |            -24.4 |                 3.73 |                  4.9  |                           677671 |
| 3 stocks, monthly, keep top 3, trend filter, 6-1m momentum    |      32.71 |                36    |               30.5  |     1.02 |              -49.1 |            -23.9 |                 4.09 |                  5.38 |                           711603 |
| 4 stocks, monthly, keep top 4, no filter, 6-1m momentum       |      30.58 |                32.46 |               29.81 |     1.02 |              -44.8 |            -22.9 |                 3.88 |                  5.1  |                           704265 |
| 6 stocks, monthly, keep top 12, no filter, 6-1m momentum      |      27    |                29.8  |               25.34 |     1.01 |              -38.4 |            -19   |                 2.08 |                  2.74 |                           539062 |
| 8 stocks, monthly, keep top 8, trend filter, 6-1m momentum    |      24.79 |                27.28 |               23.33 |     1.01 |              -36.3 |            -15.6 |                 3.14 |                  4.13 |                           489343 |
| 5 stocks, monthly, keep top 10, NO COSTS (reference)          |      28.73 |                28.59 |               28.92 |     1.01 |              -37   |            -18.5 |                 0    |                  1.53 |                           629658 |
| 3 stocks, quarterly, keep top 3, no filter, 12-1m momentum    |      31.52 |                33.33 |               30.68 |     1.01 |              -36.8 |            -11   |                 1.17 |                  1.53 |                           898191 |
| Same 38 stocks, equal weight, buy and hold                    |      21.23 |                19.91 |               22.62 |     1    |              -31   |            -25.3 |                 0.02 |                  0.02 |                           405756 |
| 5 stocks, monthly, keep top 10, trend filter, 6-1m momentum   |      28.63 |                30.67 |               27.72 |     1    |              -43.2 |            -19.1 |                 2.35 |                  3.09 |                           632057 |
| 5 stocks, monthly, keep top 5, trend filter, 6-1m momentum    |      27.79 |                30.78 |               25.99 |     1    |              -43.9 |            -26.9 |                 3.54 |                  4.66 |                           535687 |
| 8 stocks, monthly, keep top 16, no filter, 6-1m momentum      |      25.31 |                26.08 |               25.3  |     1    |              -38.4 |            -15.4 |                 1.7  |                  2.24 |                           516663 |
| 4 stocks, monthly, keep top 4, no filter, 12-1m momentum      |      29.72 |                33.08 |               27.24 |     0.99 |              -38.9 |            -11.6 |                 2.4  |                  3.16 |                           589839 |
| 4 stocks, monthly, keep top 4, trend filter, 12-1m momentum   |      29.09 |                33.91 |               25.32 |     0.99 |              -39.3 |            -23.3 |                 2.41 |                  3.17 |                           528930 |
| 3 stocks, quarterly, keep top 3, trend filter, 12-1m momentum |      30.66 |                34.38 |               28.19 |     0.99 |              -36.8 |             -8.8 |                 1.12 |                  1.48 |                           771945 |
| 8 stocks, monthly, keep top 16, trend filter, 6-1m momentum   |      24.85 |                27.14 |               23.52 |     0.99 |              -38.2 |            -15.7 |                 1.71 |                  2.24 |                           482772 |
| 6 stocks, quarterly, keep top 6, no filter, 6-1m momentum     |      26.17 |                29.38 |               23.98 |     0.99 |              -39   |            -24.7 |                 1.85 |                  2.44 |                           547214 |
| 4 stocks, monthly, keep top 8, no filter, 12-1m momentum      |      30.34 |                31.03 |               30.09 |     0.99 |              -34.1 |             -8.6 |                 1.08 |                  1.42 |                           718502 |
| 6 stocks, monthly, keep top 6, no filter, 12-1m momentum      |      26.89 |                26.82 |               27.26 |     0.98 |              -35.3 |             -5.2 |                 2.09 |                  2.75 |                           580966 |
| 3 stocks, quarterly, keep top 6, no filter, 6-1m momentum     |      30.17 |                28.42 |               32.47 |     0.98 |              -43.2 |            -25.5 |                 1.54 |                  2.02 |                           963185 |
| 3 stocks, monthly, keep top 3, trend filter, 12-1m momentum   |      30.47 |                38.61 |               24.09 |     0.98 |              -42.2 |            -22.6 |                 2.84 |                  3.73 |                           485823 |
| 4 stocks, quarterly, keep top 4, no filter, 6-1m momentum     |      28.7  |                29.23 |               28.66 |     0.98 |              -41.6 |            -27.9 |                 2.06 |                  2.71 |                           638155 |
| 5 stocks, monthly, keep top 5, no filter, 6-1m momentum       |      26.95 |                28.81 |               26.12 |     0.97 |              -43.9 |            -27.1 |                 3.55 |                  4.67 |                           540263 |
