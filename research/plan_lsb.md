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

Invested 2012-01-03, measured to 2026-11-24. All values in DKK after fees, custody, dividend tax and 17% ASK tax.
The real column is 80,000 kr put in 10 years before the end, in start-month kroner after Danish inflation.

| plan                                                          |   cagr_pct |   cagr_2012_2018_pct |   cagr_2019_now_pct |   max_drawdown_pct |   worst_year_pct |   costs_pct_per_year |   end_value_kr |   value_of_80k_after_10y_kr |   value_of_80k_after_10y_real_kr |
|:--------------------------------------------------------------|-----------:|---------------------:|--------------------:|-------------------:|-----------------:|---------------------:|---------------:|----------------------------:|---------------------------------:|
| Global index fund (Danske Invest Global Indeks, 0.40%)        |      10.59 |                 8.63 |               12.4  |              -33.4 |            -16.7 |                 0.02 |         358367 |                      206969 |                           166318 |
| S&P 500 UCITS ETF bought at Lån & Spar (foreign, custody fee) |      12.94 |                11.87 |               13.96 |              -33.1 |            -17.6 |                 0.27 |         489955 |                      235110 |                           188932 |
| Stock strategy, 4 stocks                                      |      28.03 |                23.96 |               31.64 |              -42.3 |             -9.8 |                 1.14 |        3168978 |                      807546 |                           648935 |
| Stock strategy, 4 stocks (no custody fee)                     |      28    |                23.39 |               32.1  |              -42.8 |            -13.8 |                 0.92 |        3160205 |                      797655 |                           640986 |
| Stock strategy, 6 stocks                                      |      24.29 |                20.06 |               28.11 |              -38.4 |            -14.8 |                 0.88 |        2039649 |                      643232 |                           516894 |
| Stock strategy, 6 stocks (no custody fee)                     |      24.17 |                19.76 |               28.17 |              -38.2 |            -14.5 |                 0.62 |        2010191 |                      623626 |                           501139 |
| Stock strategy, 8 stocks                                      |      21.04 |                20.48 |               21.55 |              -34.7 |            -19.5 |                 0.91 |        1374778 |                      431581 |                           346813 |
| Stock strategy, 8 stocks (no custody fee)                     |      21.78 |                20.66 |               22.75 |              -34.9 |            -19.2 |                 0.66 |        1504283 |                      474083 |                           380968 |
| Same 38 stocks, equal weight, held (survivorship baseline)    |      20.71 |                19.41 |               22.13 |              -30.9 |            -24.3 |                 0.29 |        1319655 |                      485162 |                           389871 |
| 80% global index fund + 20% stock strategy (4 stocks)         |      17.14 |                12.05 |               21.85 |              -33.1 |             -8.8 |                 0.7  |         844033 |                      399548 |                           321073 |
| 70% global index fund + 30% stock strategy (4 stocks)         |      19.6  |                14.23 |               24.53 |              -33.3 |             -7.9 |                 0.83 |        1149248 |                      490916 |                           394495 |
