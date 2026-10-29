# Coding style

Goal: every line can be explained in an interview. Simple, but nothing downgraded.

## All code
- Readable over clever. If a line needs a second read, split it.
- Clear names: `td_failed_mn`, not `x2`.
- Comments explain why, not what: `# NPCI renamed the column in 2024`.
- One job per function or query, short enough to fit on one screen.
- Only standard tools: pandas, SQL window functions, basic DAX.

## Python
- Plain functions and loops; no classes unless clearly needed.
- No `pathlib`, type hints, `from __future__` or other extras. Paths are plain strings relative to the project folder (`"data/clean/upi_bank_monthly.csv"`); run scripts from the project folder.
- Steps in order: load → clean → check → save, each its own function.
- Every check that matters stays (percentages add to 100, no duplicate bank-months, missing months listed).

## SQL (PostgreSQL)
- One file per business question, with a one-line comment saying which question it answers.
- CTEs (`WITH ... AS`) in readable steps instead of nested subqueries.
- Volume-weighted averages, never a simple average of percentages.

## DAX (Power BI)
- One measure per idea, named the way a manager would say it: `TD %`, `TD % vs Industry`.
- `DIVIDE()` instead of `/` so blanks never break a visual.

## No downgrading
Simple does not mean weaker. Tests, validation and correct maths stay; they are just written plainly.
