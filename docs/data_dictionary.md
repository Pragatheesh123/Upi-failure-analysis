# Data dictionary

Range: Aug 2021 → Sep 2026 for banks (62 months), Jan 2022 → Sep 2026 for apps and P2P/P2M (57 months).
Built by `python python/step2_clean_data.py` from `data/raw/` and `data/bank_names.csv`. `excel/upi_clean_data.xlsx` holds the same tables plus a "Before vs after" sheet (NPCI value next to clean value, changed cells red) and the name lists. App spellings are mapped with `data/app_names.csv` (app_raw, app), built the same way as `data/bank_names.csv`.

## data/clean/upi_bank_monthly.csv — one row per bank per month (3,100 rows, 15 columns)

Cleaning only. The calculated columns are added in SQL (see the view `bank_details` below).

| # | Column | Type | Source | Meaning |
|---|---|---|---|---|
| 1 | month | YYYY-MM | NPCI | Reporting month |
| 2 | bank_raw | text | NPCI | Bank name exactly as NPCI wrote it (after the 2 logged corrections) |
| 3 | bank | text | `bank_names.csv` | One standard name per bank (215 spellings → 68 banks) |
| 4 | bank_type | text | `bank_names.csv` | Public, Private, Small finance, Payments bank, Gramin, Foreign, Co-operative, Payment company (PPI), Credit card issuer |
| 5 | rank_in_source | int | NPCI | Position in NPCI's table (by volume) |
| 6 | total_volume_mn | float | NPCI | UPI payments started from this bank, millions |
| 7 | approved_pct | float | NPCI | % approved |
| 8 | bd_pct | float | NPCI | % business decline (user side) |
| 9 | td_pct | float | NPCI | % technical decline (bank or NPCI systems) |
| 10 | debit_reversal_count_mn | float | NPCI | Debited-then-failed payments needing a refund, millions ("-" in NPCI → blank) |
| 11 | debit_reversal_success_pct | float | NPCI | % of those refunds that succeeded ("NaN%" in NPCI → blank; Aug 2022 divided by 100 because NPCI dropped the decimal point, e.g. "9123.00%" → 91.23) |
| 12 | udir_auto_update_sr_pct | float | NPCI | % of failed payments resolved online through UDIR (recent months only) |
| 13 | udir_refund_sr_pct | float | NPCI | % of refunds processed online through UDIR (recent months only) |
| 14 | source | text | Added | `npci_api` (2022 on) or `npci_archive_2021_provisional` (Aug–Dec 2021) |
| 15 | is_name_corrected | bool | Cleaning section 3 | True on the 2 rows where NPCI printed the wrong bank name |

## data/clean/upi_bank_value_monthly.csv — approved payments and value per bank (2,814 rows, 5 columns)

From NPCI's "Top 50 Member Vol & Val" table (Jan 2022 on), with standard bank names; "Total" and "Others" rows dropped. A few months list a bank name twice (e.g. two Grameena banks with one spelling), so there is no one-row-per-bank rule here.

| Column | Type | Meaning |
|---|---|---|
| month | YYYY-MM | Reporting month |
| bank_raw | text | Name as NPCI wrote it |
| bank | text | Standard name from `bank_names.csv` |
| approved_volume_mn | float | Approved payments, millions (this table counts approved payments only) |
| value_cr | float | Value of those payments, ₹ crore |

## SQL view bank_details (sql/02_extra_columns.sql) — all 15 bank columns plus

| Column | Meaning |
|---|---|
| year | First 4 characters of month |
| approved_mn | total_volume_mn × approved_pct ÷ 100 |
| user_failed_mn | total_volume_mn × bd_pct ÷ 100 (BD = user failures) |
| system_failed_mn | total_volume_mn × td_pct ÷ 100 (TD = system failures) |
| is_festival_month | Month is October or November |
| above_npci_target | td_pct > 1 (NPCI OC 149, May 2022) |
| bank_group | bank_type for comparisons: Public, Private, Payments bank, Gramin, Small finance, Foreign, and Others (Co-operative + Payment company (PPI) + Credit card issuer) |

The ₹ value of failures (question 4) is worked out in that question's query: join `bank_value_monthly` on month and bank where its approved_volume_mn is within 2% of approved_mn; average payment = value_cr × 10 ÷ approved_volume_mn. This covers 94.7% of system-failed payments.

## data/clean/upi_app_monthly.csv — one row per app per month (4,349 rows, 5 columns)

| Column | Type | Meaning |
|---|---|---|
| month | YYYY-MM | Reporting month |
| app | text | App name from `data/app_names.csv` (footnote marks removed). NPCI lists a few apps twice in some months (e.g. Bajaj Finserv, Feb 2023); both rows are kept |
| volume_mn | float | Total volume, millions |
| value_cr | float | Total value, ₹ crore |
| app_share_pct | float | Calculated: app volume ÷ all apps' volume that month × 100 |

## data/clean/upi_p2p_p2m_monthly.csv — one row per month (57 rows, 7 columns)

| Column | Type | Meaning |
|---|---|---|
| month | YYYY-MM | Reporting month |
| p2p_volume_mn | float | Person-to-person volume, millions |
| p2p_value_cr | float | Person-to-person value, ₹ crore |
| p2m_volume_mn | float | Person-to-merchant volume, millions |
| p2m_value_cr | float | Person-to-merchant value, ₹ crore |
| total_volume_mn | float | NPCI's monthly total (check: P2P + P2M = total within 1 Mn) |
| p2m_share_pct | float | Calculated: P2M ÷ (P2P + P2M) × 100 (used for question 5, checkout payments at risk) |

## data/bank_names.csv

bank_raw → bank, bank_type: every spelling NPCI used in the bank table and the vol & val table (218 spellings → 68 banks). A new spelling stops the cleaning script until it is added. The 2 NPCI name fixes are written inside `python/step2_clean_data.py` (step 3).
