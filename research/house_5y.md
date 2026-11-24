# 80,000 kr, 5 years, paying off a house: what actually happened

80,000 kr and a 5-year goal: pay off the house. Invest on an aktiesparekonto, or pay down the loan?

    python research/house_5y.py        # needs Yahoo Finance (Actions -> Backtest, script house_5y)

Every 5-year window starting each month since 1993 is tested for these plans:
  A  Pay down the mortgage now: a guaranteed return equal to the loan's interest + contribution fee after
     the ~33% interest deduction.
  B  100% global/US index fund on the aktiesparekonto for 5 years (Danish-listed fund, 0.40% a year,
     Lån & Spar: 0.10% min 29 kr per trade, 17% ASK tax each year with losses carried forward).
  C  Half and half: 40,000 kr off the loan now, 40,000 kr in the index fund.
  D  Index fund, then de-risk: sell a third at the start of years 4 and 5 and the rest at the end,
     each sale going straight onto the loan (so it earns the loan rate from then on).
  E  Index fund with a stop: sell everything and pay down the loan once the account is up 25% after tax.

Index data: SPY (S&P 500) total return from 1993, and iShares MSCI World (URTH) from 2012, converted to
DKK where the exchange rate exists. US stocks did unusually well in this period, so B's history is
flattering. Results are a range of what happened, not a forecast. Not investment advice.

Values are the debt removed after 5 years, in kroner, compared like for like: money put on the loan counts
at its interest saved after the deduction. Windows: S&P 500 (1993-): 347 windows, 1993-02-28 to 2026-11-30; MSCI World (2012-): 119 windows, 2012-02-29 to 2026-11-30

## S&P 500 (1993-), loan rate 3.0% (F3/F5 + fee)

| plan                                  |   median_kr |   worst_10pct_kr |   worst_kr |   best_kr |   pct_windows_beat_paydown |   pct_windows_below_80k |
|:--------------------------------------|------------:|-----------------:|-----------:|----------:|---------------------------:|------------------------:|
| A  Pay down the loan now              |       88370 |            88370 |      88370 |     88370 |                          0 |                       0 |
| B  Index fund for 5 years             |      123925 |            72148 |      53372 |    227370 |                         72 |                      21 |
| C  Half loan, half index fund         |      106054 |            80231 |      70830 |    157716 |                         72 |                       9 |
| D  Index fund, sell down in years 4-5 |      120262 |            72773 |      59543 |    195731 |                         76 |                      19 |
| E  Index fund, cash out at +25%       |      105312 |            80604 |      66496 |    112657 |                         84 |                      10 |

## S&P 500 (1993-), loan rate 3.8% (F5 + fee)

| plan                                  |   median_kr |   worst_10pct_kr |   worst_kr |   best_kr |   pct_windows_beat_paydown |   pct_windows_below_80k |
|:--------------------------------------|------------:|-----------------:|-----------:|----------:|---------------------------:|------------------------:|
| A  Pay down the loan now              |       90716 |            90716 |      90716 |     90716 |                          0 |                       0 |
| B  Index fund for 5 years             |      123925 |            72148 |      53372 |    227370 |                         71 |                      21 |
| C  Half loan, half index fund         |      107227 |            81404 |      72003 |    158890 |                         71 |                       6 |
| D  Index fund, sell down in years 4-5 |      120816 |            73124 |      59825 |    196688 |                         74 |                      19 |
| E  Index fund, cash out at +25%       |      107252 |            80604 |      66496 |    114904 |                         84 |                      10 |

## S&P 500 (1993-), loan rate 4.6% (fixed + fee)

| plan                                  |   median_kr |   worst_10pct_kr |   worst_kr |   best_kr |   pct_windows_beat_paydown |   pct_windows_below_80k |
|:--------------------------------------|------------:|-----------------:|-----------:|----------:|---------------------------:|------------------------:|
| A  Pay down the loan now              |       93112 |            93112 |      93112 |     93112 |                          0 |                       0 |
| B  Index fund for 5 years             |      123925 |            72148 |      53372 |    227370 |                         70 |                      21 |
| C  Half loan, half index fund         |      108424 |            82602 |      73201 |    160087 |                         70 |                       3 |
| D  Index fund, sell down in years 4-5 |      121373 |            73477 |      60107 |    197648 |                         73 |                      19 |
| E  Index fund, cash out at +25%       |      109147 |            80604 |      66496 |    117184 |                         83 |                      10 |

## MSCI World (2012-), loan rate 3.0% (F3/F5 + fee)

| plan                                  |   median_kr |   worst_10pct_kr |   worst_kr |   best_kr |   pct_windows_beat_paydown |   pct_windows_below_80k |
|:--------------------------------------|------------:|-----------------:|-----------:|----------:|---------------------------:|------------------------:|
| A  Pay down the loan now              |       88370 |            88370 |      88370 |     88370 |                          0 |                       0 |
| B  Index fund for 5 years             |      128217 |           115510 |      88444 |    152748 |                        100 |                       0 |
| C  Half loan, half index fund         |      108173 |           101844 |      88364 |    120462 |                         99 |                       0 |
| D  Index fund, sell down in years 4-5 |      117153 |           108734 |      92566 |    141103 |                        100 |                       0 |
| E  Index fund, cash out at +25%       |      105421 |           102980 |     101614 |    112309 |                        100 |                       0 |

## MSCI World (2012-), loan rate 3.8% (F5 + fee)

| plan                                  |   median_kr |   worst_10pct_kr |   worst_kr |   best_kr |   pct_windows_beat_paydown |   pct_windows_below_80k |
|:--------------------------------------|------------:|-----------------:|-----------:|----------:|---------------------------:|------------------------:|
| A  Pay down the loan now              |       90716 |            90716 |      90716 |     90716 |                          0 |                       0 |
| B  Index fund for 5 years             |      128217 |           115510 |      88444 |    152748 |                         99 |                       0 |
| C  Half loan, half index fund         |      109346 |           103017 |      89537 |    121635 |                         99 |                       0 |
| D  Index fund, sell down in years 4-5 |      117741 |           109277 |      93059 |    141799 |                        100 |                       0 |
| E  Index fund, cash out at +25%       |      107112 |           104008 |     102193 |    114498 |                        100 |                       0 |

## MSCI World (2012-), loan rate 4.6% (fixed + fee)

| plan                                  |   median_kr |   worst_10pct_kr |   worst_kr |   best_kr |   pct_windows_beat_paydown |   pct_windows_below_80k |
|:--------------------------------------|------------:|-----------------:|-----------:|----------:|---------------------------:|------------------------:|
| A  Pay down the loan now              |       93112 |            93112 |      93112 |     93112 |                          0 |                       0 |
| B  Index fund for 5 years             |      128217 |           115510 |      88444 |    152748 |                         99 |                       0 |
| C  Half loan, half index fund         |      110544 |           104215 |      90735 |    122833 |                         99 |                       0 |
| D  Index fund, sell down in years 4-5 |      118340 |           109823 |      93554 |    142497 |                        100 |                       0 |
| E  Index fund, cash out at +25%       |      108849 |           105182 |     102772 |    116718 |                        100 |                       0 |
