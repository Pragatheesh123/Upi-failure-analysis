# Raw data sources

## npci_archive_2021_remitter_provisional.csv  (PROVISIONAL)

- **What:** NPCI "UPI Remitter Banks" tables, Mar–Dec 2021. Top 30 banks for Mar–Jul, top 50 for Aug–Dec. 400 rows.
- **From:** https://npci.org.in/what-we-do/upi/upi-ecosystem-statistics/archives, read on 28 Oct 2026 through a web-reading tool (the project workspace could not download the page directly).
- **Bank names:** kept exactly as NPCI wrote them (cleaning happens in Week 1).
- **Checks passed:** Approved + BD + TD = 100% (±0.02) on every row; volumes in descending order within each month; ranks 1..N with no gaps; no duplicate bank-months.
- **Why provisional:** the page went through a summarising tool, not a direct download. Before any finding is published, re-download the archive page on a laptop (`python python/check_sample.py`) and compare. Replace this file if anything differs.
- **Not included:** Feb 2021 and earlier (page text was cut off), beneficiary tables, app tables.

## npci_api/  (Jan 2022 → Sep 2026)

- **What:** NPCI UPI ecosystem statistics, 4 tables, one JSON file per month per page (10 rows per page), saved exactly as received:
  `remitter/` (Top 50 remitter banks), `member_vol_val/` (Top 50 member volume and value), `p2p_p2m/`, `apps/`.
- **From:** `https://www.npci.org.in/api/ecosystem-statistics/get-statistics?product_name=UPI&tab_name=...&year=...&month=...`, the same feed the NPCI website uses. No login.
- **When:** 28 Oct 2026. Every request (URL, time, HTTP status, saved file) is in `npci_api/manifest.csv`.
- **Made by:** `python python/step1_get_raw_data.py` (rerunnable; skips files already saved).
- **Combined copies:** `npci_remitter.csv`, `npci_member_vol_val.csv`, `npci_p2p_p2m.csv`, `npci_apps.csv`: all pages of each table in one file, values exactly as in the JSON (as text), plus `file_month`. Rebuilt by step 1 every run.
- **Checks passed:** all 57 months present in all 4 tables; each month has as many rows as NPCI's `totalCount`; the month inside every row matches the file name; remitter Approved + BD + TD = 100% (±0.05) on all 2,850 rows.

## Known gaps in NPCI's own tables (kept missing, not filled in)

- **Jan 2026, remitter table:** NPCI leaves out Uttar Pradesh Gramin Bank (it was "Baroda U.P. Bank" before the 1 May 2025 merger). The raw files `npci_api/remitter/2026-01_p*.json` have 50 other banks. The same bank is in NPCI's Jan 2026 volume & value table (69.6 mn approved payments, Rs 6,122.89 crore), so it should have been in the top 50. Effect: the Gramin last-12-month figures miss one month of their worst bank, so they are slightly too low.
- **Gramin bank merger, 1 May 2025** ("One State, One RRB", gazette 7 Apr 2025; Business Standard, 1 May 2025: https://www.business-standard.com/finance/news/regional-rural-bank-one-state-one-rrb-may-1-details-125050100627_1.html). NPCI keeps switching between old and new names after the merger. From 2025-05, `python/step2_clean_data.py` counts Baroda U.P. Bank as Uttar Pradesh Gramin Bank; Andhra Pragathi, Chaitanya Godavari and Andhra Pradesh Grameena Vikas as Andhra Pradesh Grameena Bank; Rajasthan Marudhara as Rajasthan Gramin Bank. The official gazette is still to be opened.
