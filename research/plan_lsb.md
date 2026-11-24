# 80,000 kr on a Lån & Spar aktiesparekonto: plan backtest

Backtest plans for 80,000 kr on an aktiesparekonto at Lån & Spar Bank.

    python research/plan_lsb.py        # needs Yahoo Finance (run it via Actions -> Backtest, script plan_lsb)

Lån & Spar online prices (lsb.dk/dine-vilkaar/gebyrlisten, read 24 Nov 2026):
- Danish-listed shares and funds: 0.10%, min 29 kr; 7.50 kr per holding change; no custody fee (VP)
- US and other foreign shares: 0.20%, min 29 kr; currency +/- 1.30 kr per 100 USD (~0.19%)
- Foreign shares held outside VP: 0.25% a year, min 250 kr
Index funds: Danske Invest Global Indeks (MSCI World) costs 0.40% a year, Lån & Spar Invest Globale
Aktier Basis 0.44%. Modelled with iShares MSCI World (URTH, 0.24%) total returns, adjusted to 0.40%.

Same caveats as backtest.py: the stock universe is today's survivors, and the skill's fundamental score
cannot be backtested. Compare plans with each other and with the index fund, not as forecasts.

Invested 2012-01-03, measured to 2026-11-23. All values in DKK after fees, custody, dividend tax and 17% ASK tax.

| plan                                                          |   cagr_pct |   cagr_2012_2018_pct |   cagr_2019_now_pct |   max_drawdown_pct |   worst_year_pct |   costs_pct_per_year |   end_value_kr |   value_of_80k_after_10y_kr |
|:--------------------------------------------------------------|-----------:|---------------------:|--------------------:|-------------------:|-----------------:|---------------------:|---------------:|----------------------------:|
| Global index fund (Danske Invest Global Indeks, 0.40%)        |      10.62 |                 8.63 |               12.45 |              -33.4 |            -16.7 |                 0.02 |         359480 |                      209693 |
| S&P 500 UCITS ETF bought at Lån & Spar (foreign, custody fee) |      12.98 |                11.87 |               14.03 |              -33.1 |            -17.6 |                 0.27 |         492266 |                      238680 |
| Stock strategy, 4 stocks                                      |      28.18 |                23.96 |               31.94 |              -42.3 |             -9.8 |                 1.15 |        3223447 |                      826937 |
| Stock strategy, 4 stocks (no custody fee)                     |      28.16 |                23.39 |               32.4  |              -42.8 |            -13.8 |                 0.92 |        3214557 |                      816819 |
| Stock strategy, 6 stocks                                      |      24.38 |                20.06 |               28.27 |              -38.4 |            -14.8 |                 0.88 |        2058598 |                      653312 |
| Stock strategy, 6 stocks (no custody fee)                     |      24.21 |                19.76 |               28.24 |              -38.2 |            -14.5 |                 0.62 |        2017553 |                      630008 |
| Stock strategy, 8 stocks                                      |      21.05 |                20.48 |               21.55 |              -34.7 |            -19.5 |                 0.91 |        1374387 |                      434046 |
| Stock strategy, 8 stocks (no custody fee)                     |      21.79 |                20.66 |               22.78 |              -34.9 |            -19.2 |                 0.66 |        1506137 |                      477713 |
| Same 38 stocks, equal weight, held (survivorship baseline)    |      20.78 |                19.41 |               22.25 |              -30.9 |            -24.3 |                 0.29 |        1329567 |                      494092 |
| 80% global index fund + 20% stock strategy (4 stocks)         |      17.24 |                12.05 |               22.04 |              -33.1 |             -8.8 |                 0.7  |         854533 |                      408114 |
| 70% global index fund + 30% stock strategy (4 stocks)         |      19.71 |                14.23 |               24.76 |              -33.3 |             -7.9 |                 0.83 |        1165401 |                      502008 |
