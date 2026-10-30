# Coding style

Goal: every line can be explained in an interview. Simple, but nothing downgraded.

## All code
- Readable over clever. If a line needs a second read, split it.
- Clear names that say what the thing is: `system_failed_mn`, `user_fail_pct`, `bank_details`, not `td_failed_mn`, `c`, `x2`. Table aliases short but readable (`b`, `y2022`).
- Comments explain why, not what: `# NPCI renamed the column in 2024`.
- One job per function or query, short enough to fit on one screen.
- Only standard tools: pandas, SQL window functions, basic DAX.

## Python
- Cleaning and analysis: plain pandas, top to bottom, a comment per step. No `def` functions; repeated work goes in a plain `for` loop. Read data with `pd.read_csv`.
- No `pathlib`, type hints, `from __future__` or other extras. Paths are plain strings relative to the project folder (`"data/clean/upi_bank_monthly.csv"`); run scripts from the project folder.
- Steps in order: load → clean → check → save, each a commented block.
- Every check that matters stays (percentages add to 100, no duplicate bank-months, missing months listed).

## SQL (PostgreSQL)
- Simple queries: `SELECT ... FROM ... WHERE ... GROUP BY ... ORDER BY`, plain `JOIN`, `CASE`, `BETWEEN`. No stacked `WITH` blocks.
- Calculations are written once in the view `bank_details`; question files just read from it.
- Window functions (`RANK`, `LAG`) only when a question needs them, one simple one per query.
- One file per business question, starting with a one-line comment saying which question it answers.
- Volume-weighted %: `SUM(failed) / SUM(total)`, never `AVG` of percentages.

## DAX (Power BI)
- One measure per idea, named the way a manager would say it: `TD %`, `TD % vs Industry`.
- `DIVIDE()` instead of `/` so blanks never break a visual.

## No downgrading
Simple does not mean weaker. Tests, validation and correct maths stay; they are just written plainly.
