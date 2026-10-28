# Data dictionary

Range: Aug 2021 → latest published month (~62 months). Totals are estimates until collection; exact counts go in the README.

## data/clean/upi_bank_monthly.csv — one row per bank per month (~3,100 rows, 18 columns)

| # | Column | Type | Source | Meaning |
|---|---|---|---|---|
| 1 | month | YYYY-MM | NPCI table title | Reporting month |
| 2 | bank_raw | text | NPCI | Bank name exactly as NPCI wrote it |
| 3 | bank | text | Cleaning | One standard name per bank (lookup table) |
| 4 | bank_type | text | Added | Public, Private, Payments, Small finance, Gramin, Foreign, Co-operative |
| 5 | rank_in_source | int | NPCI | Position in NPCI's table (by volume) |
| 6 | total_volume_mn | float | NPCI | UPI payments started from this bank, millions |
| 7 | approved_pct | float | NPCI | % approved |
| 8 | bd_pct | float | NPCI | % business decline (user side) |
| 9 | td_pct | float | NPCI | % technical decline (bank or NPCI systems) |
| 10 | debit_reversal_count_mn | float | NPCI | Debited-then-failed payments needing a refund, millions |
| 11 | debit_reversal_success_pct | float | NPCI | % of those refunds that succeeded |
| 12 | approved_mn | float | Calculated | total_volume_mn × approved_pct / 100 |
| 13 | bd_failed_mn | float | Calculated | total_volume_mn × bd_pct / 100 |
| 14 | td_failed_mn | float | Calculated | total_volume_mn × td_pct / 100 |
| 15 | is_festival_month | bool | Added | Month is October or November |
| 16 | above_npci_target | bool | Added | td_pct > 1.0 (NPCI circular OC 149A) |
| 17 | avg_payment_value_inr | float | RBI-hosted NPCI files | Bank's value ÷ volume as remitter that month (estimate input) |
| 18 | td_failed_value_cr | float | Calculated | td_failed_mn × avg_payment_value_inr ÷ 10 (₹ crore; an estimate) |

Checks: approved + bd + td = 100 (±0.05), which also catches NPCI's reported Aug 2022 decimal error; no duplicate (month, bank); missing months listed, never filled; each month's source recorded.

## data/clean/upi_app_monthly.csv — one row per app per month (~3,500 rows, 5 columns)

| Column | Type | Meaning |
|---|---|---|
| month | YYYY-MM | Reporting month |
| app | text | App name (cleaned) |
| volume_mn | float | Total volume, millions |
| value_cr | float | Total value, ₹ crore |
| app_share_pct | float | Calculated: app volume ÷ all apps' volume that month |

## data/clean/upi_p2p_p2m_monthly.csv — one row per month (62 rows, 6 columns)

| Column | Type | Meaning |
|---|---|---|
| month | YYYY-MM | Reporting month |
| p2p_volume_mn | float | Person-to-person volume, millions |
| p2p_value_cr | float | Person-to-person value, ₹ crore |
| p2m_volume_mn | float | Person-to-merchant volume, millions |
| p2m_value_cr | float | Person-to-merchant value, ₹ crore |
| p2m_share_pct | float | Calculated: P2M ÷ total volume (used for question 5, checkout payments at risk) |

## Totals (estimated)

~6,660 rows, ~73,700 data points across the three tables.
