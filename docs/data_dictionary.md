# Data dictionary

Range: Aug 2021 → Sep 2026 for banks (62 months), Jan 2022 → Sep 2026 for apps and P2P/P2M (57 months).
Built by `python python/step2_clean_data.py` from `data/raw/` and `data/bank_names.csv`. `excel/upi_clean_data.xlsx` holds the same tables plus a "Changes made" sheet.

## data/clean/upi_bank_monthly.csv — one row per bank per month (3,100 rows, 22 columns)

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
| 10 | debit_reversal_count_mn | float | NPCI | Debited-then-failed payments needing a refund, millions |
| 11 | debit_reversal_success_pct | float | NPCI | % of those refunds that succeeded |
| 12 | approved_mn | float | Calculated | total_volume_mn × approved_pct / 100 |
| 13 | bd_failed_mn | float | Calculated | total_volume_mn × bd_pct / 100 |
| 14 | td_failed_mn | float | Calculated | total_volume_mn × td_pct / 100 |
| 15 | is_festival_month | bool | Added | Month is October or November |
| 16 | above_npci_target | bool | Added | td_pct > 1.0 (NPCI circular OC 149A) |
| 17 | avg_payment_value_inr | float | NPCI "Top 50 Member Vol & Val" | ₹ per successful payment = value_cr × 10 ÷ volume_mn. Used only when that table's volume matches approved_mn within 2%; blank otherwise (and for 2021). Covers 94.7% of system-failed payments |
| 18 | td_failed_value_cr | float | Calculated | td_failed_mn × avg_payment_value_inr ÷ 10 (₹ crore; an estimate) |
| 19 | udir_auto_update_sr_pct | float | NPCI | % of failed payments resolved online through UDIR (recent months only) |
| 20 | udir_refund_sr_pct | float | NPCI | % of refunds processed online through UDIR (recent months only) |
| 21 | source | text | Added | `npci_api` (2022 on) or `npci_archive_2021_provisional` (Aug–Dec 2021) |
| 22 | is_name_corrected | bool | Cleaning step 3 | True on the 2 rows where NPCI printed the wrong bank name |

Checks (the script stops if any fails): approved + bd + td = 100 (±0.05); no duplicate (month, bank); no missing month; 50 banks every month.

## data/clean/upi_app_monthly.csv — one row per app per month (4,349 rows, 5 columns)

| Column | Type | Meaning |
|---|---|---|
| month | YYYY-MM | Reporting month |
| app | text | App name: footnote marks removed, the spelling NPCI used most recently |
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
