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
data/raw/      files exactly as downloaded (HTML/PDF)
data/clean/    tidy CSVs: one row per bank per month
src/           Python: collect, parse, clean
sql/           PostgreSQL schema and analysis queries
notebooks/     statistics and charts
excel/         cost-of-failure what-if model
powerbi/       dashboard (.pbix) and screenshots
docs/          data check, data dictionary, notes
tests/         parser tests on real sample rows
```

## Tools

Python (pandas, BeautifulSoup, pdfplumber, SciPy) · PostgreSQL (window functions) · Excel · Power BI (DAX)

## Run it

```bash
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest                                  # parser tests
python src/check_sample.py              # Week 0: what months does NPCI have?
```

## Findings

_Coming in Week 5._

## Sources

National Payments Corporation of India (NPCI), UPI Ecosystem Statistics. Reserve Bank of India, NPCI data for publication.
