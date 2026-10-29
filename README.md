# Where Does UPI Fail? A Bank-wise Payment Failure Analysis

> Status: **Week 0 — data checked, repo set up.** Findings will be added in Week 5.

My own UPI payments kept failing, so I analysed which banks cause it, using NPCI's monthly statistics.

## The funnel

```
Payment started (Total Volume)
 ├─ Approved                         Approved %
 ├─ Failed: business decline (BD)    wrong PIN, low balance, limit crossed  → user side
 └─ Failed: technical decline (TD)   bank or NPCI system/network error      → system side
```

## Questions

1. Which banks have the highest technical decline rate, and are they improving?
2. Are technical declines higher in festival months (Oct–Nov)?
3. How many payments failed in a year for technical reasons (the cost of failure)?
4. How concentrated is the UPI app market?

## Data

| Source | What | Format |
|---|---|---|
| [NPCI UPI Ecosystem Statistics](https://www.npci.org.in/what-we-do/upi/upi-ecosystem-statistics) and [archive](https://npci.org.in/what-we-do/upi/upi-ecosystem-statistics/archives) | Monthly top remitter/beneficiary banks with Approved, BD and TD %; app volumes | HTML tables |
| RBI-hosted NPCI monthly data | Entity-wise volumes and values (cross-check) | PDF |

Time range: _to be confirmed in Week 0 (recommended Aug 2021 → latest)._
Every number in this repo comes from these files. Missing months are listed, never filled in.
See [`docs/week0_data_check.md`](docs/week0_data_check.md) for the data check and known limits.

## Repo layout

```
data/raw/            NPCI files exactly as downloaded, plus one raw CSV per table (values as text)
data/bank_names.csv  every bank spelling NPCI used -> one standard name and bank type
data/app_names.csv   every app spelling NPCI used -> one standard app name
data/clean/          clean tables (CSV) used by SQL and Power BI
python/              step1_get_raw_data.py, step2_clean_data.py
sql/                 01_create_tables.sql (load clean CSVs), 02_bank_monthly_calc.sql (calculated columns), queries next
excel/               upi_clean_data.xlsx (changes made, before vs after, clean tables), cost model later
powerbi/             dashboard (later)
docs/                decisions log, data dictionary, notes
```

## Tools

Python (pandas) · PostgreSQL (window functions) · Excel · Power BI (DAX)

## Run it

```bash
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
python python/step1_get_raw_data.py     # download NPCI data (skips files already saved)
python python/step2_clean_data.py       # build data/clean/, stops if any check fails
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d upi_failure -f sql/01_create_tables.sql   # load into PostgreSQL (asks for the password)
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d upi_failure -f sql/02_bank_monthly_calc.sql  # calculated columns
```

## Findings

_Coming in Week 5._

## Sources

National Payments Corporation of India (NPCI), UPI Ecosystem Statistics. Reserve Bank of India, NPCI data for publication.
