# Week 0 — Data check

Checked: 28 Oct 2026. Goal: confirm at least 12 months of bank-wise decline rates exist before building anything.

**Verdict: yes.** NPCI publishes a monthly remitter-bank table with exactly the funnel columns this project needs, from at least Feb 2021 to Sep 2026. Things still to confirm on your own laptop are marked ☐.

## What the remitter table contains

One row per bank per month, for the top banks by volume:

| NPCI column | Our column | Funnel meaning |
|---|---|---|
| UPI Remitter Banks / Members | `bank` | the payer's bank |
| Total Volume (In Mn) | `total_volume_mn` | payments started |
| Approved % | `approved_pct` | succeeded |
| BD % | `bd_pct` | failed — business decline (wrong PIN, low balance, limit crossed) |
| TD % | `td_pct` | failed — technical decline (bank or NPCI systems/network) |
| Total Debit Reversal Count (In Mn) | `debit_reversal_count_mn` | money debited then had to be returned |
| Debit Reversal Success % | `debit_reversal_success_pct` | share of those refunds that went through |

Approved + BD + TD adds to 100% (checked on real rows, e.g. SBI Dec 2021: 88.63 + 6.94 + 4.43). The debit-reversal columns are a bonus: a second "bank's fault" signal nobody else's project will use.

There is also a **beneficiary** table (payee's bank) with Approved/BD/TD/Deemed Approved %, and a **UPI Apps** table (volume and value per app) for question 4.

## Sources found

| Source | Status | Use |
|---|---|---|
| [NPCI archive](https://npci.org.in/what-we-do/upi/upi-ecosystem-statistics/archives) | HTML tables, one block per month; seen Feb 2021 → Dec 2021 at the top of the page | Primary |
| [NPCI ecosystem statistics](https://www.npci.org.in/what-we-do/upi/upi-ecosystem-statistics) | Page uses tabs; a non-browser fetch only returned a Sep 2024 merchant-category table | Primary for recent months ☐ |
| RBI-hosted "NPCI data for publication" PDFs | Search snippets show entity-wise **volumes and values**, not decline % | Cross-check volumes only ☐ |
| [dataful.in #445](https://dataful.in/datasets/445/) (remitter) / [#342](https://dataful.in/datasets/342/) (beneficiary) | Same NPCI columns, FY 2019-20 → 2026-27, ~3,670 rows; sample rows reach Sep 2026 | Cross-check only, as the plan says |

## Format changes to handle in Week 1

1. **Coverage changed:** "Top 30 Banks" up to Jul 2021, **"Top 50" from Aug 2021**.
2. **Renamed:** "Remitter Banks" → **"Remitter Members"** by Oct 2024 (the checker flags this as a second layout).
3. **Month label varies:** `(December'21)`, `(Oct'24)`, `(December-2021)`, `(Oct-2024)`. Parser handles all four.
4. **Bank names vary:** `State Bank Of India` / `STATE BANK OF INDIA`, `HDFC BANK LTD` / `HDFC BANK LTD.`, `Axis Bank Ltd` / `Axis Bank Ltd.` → needs a bank-name lookup table.
5. **Header spacing:** `BD %` vs `BD%`, `TD %` vs `TD%`.
6. **Mergers:** Andhra Bank still appears in the 2021 tables (seen up to May 2021) although it merged into Union Bank of India in April 2020. Keep it as its own row; don't add its numbers to Union Bank.

## Limits to state honestly in the README

- **Only the top 30/50 banks are published.** "Industry average" means the volume-weighted average of the published banks, not all of UPI. Smaller banks drop in and out of the list, so some bank-months are missing for real reasons.
- **The data is monthly.** It cannot show salary days or month-ends. Question 2 should become: *"Are technical declines higher in festival months (Oct–Nov)?"* ← suggested change to the plan.
- **TD % includes NPCI-side failures**, not only the bank's. NPCI's own definition says "technical reasons… on bank or NPCI side". Say "bank or network" in findings, not "the bank's fault" alone.
- **NPCI's targets** to compare against: TD below 1% and BD below 5% (NPCI circular OC 149A, June 2022). Useful as a reference line on the dashboard.

## Time range: answer to the open comment in the plan

Recommendation: **Aug 2021 → latest month (Sep 2026)**, not Jan 2024.

- Jan 2024 → Sep 2026 gives only **2 festival seasons** (2024, 2025) = 4 festival months. A t-test on 4 points is weak.
- Aug 2021 → Sep 2026 gives **5 seasons** (2021–2025) = 10 festival months, ~62 months total, all in the same Top 50 format.
- Fallback: if the archive turns out not to have 2022–2023, use Jan 2024 → latest and say the festival test is exploratory.

## ☐ Still to do on your laptop (30–60 min)

1. `python src/check_sample.py` — fetches the archive page, saves it in `data/raw/`, prints months found, gaps and layouts.
   If it says "no table found", open the page in your browser, Ctrl+S → "Webpage, complete", then
   `python src/check_sample.py --file path/to/saved.html`.
2. Do the same for the main ecosystem-statistics page (recent months). If NPCI has moved it to a new address, update the URL in `src/check_sample.py`.
3. Open one RBI "NPCI data for publication" PDF and confirm whether it has BD/TD columns (I could not open it from here).
4. Pick the time range, record it in the README, commit.
