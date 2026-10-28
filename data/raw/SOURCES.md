# Raw data sources

## npci_archive_2021_remitter_provisional.csv  (PROVISIONAL)

- **What:** NPCI "UPI Remitter Banks" tables, Mar–Dec 2021. Top 30 banks for Mar–Jul, top 50 for Aug–Dec. 400 rows.
- **From:** https://npci.org.in/what-we-do/upi/upi-ecosystem-statistics/archives, read on 28 Oct 2026 through a web-reading tool (the project workspace could not download the page directly).
- **Bank names:** kept exactly as NPCI wrote them (cleaning happens in Week 1).
- **Checks passed:** Approved + BD + TD = 100% (±0.02) on every row; volumes in descending order within each month; ranks 1..N with no gaps; no duplicate bank-months.
- **Why provisional:** the page went through a summarising tool, not a direct download. Before any finding is published, re-download the archive page on a laptop (`python src/check_sample.py`) and compare. Replace this file if anything differs.
- **Not included:** Feb 2021 and earlier (page text was cut off), beneficiary tables, app tables.

## Still needed

- Jan 2022 → latest month: only on the live NPCI statistics page, which loads tables in a browser.
