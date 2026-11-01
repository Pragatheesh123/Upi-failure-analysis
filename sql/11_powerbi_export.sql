-- Saves the tables Power BI needs as CSV files in powerbi/data/.
-- Power BI then only adds things up; every calculated column comes from 02_extra_columns.sql.
-- Run with psql (like 01 and 10):
-- & "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d upi_failure -f sql/11_powerbi_export.sql

-- Page 2 "why" chart: for each change, how much came from banks themselves (same as 04_q2).
-- The rest of the change = payments moving between banks.
-- (SELECT ...) inside the SELECT gives one number from a small query: here the overall % of one year.
DROP TABLE IF EXISTS why_split;
CREATE TABLE why_split (step INT, change TEXT, total_change NUMERIC, from_banks_themselves NUMERIC);

INSERT INTO why_split
SELECT 1, 'System failure %, 2022 → 2025',
    (SELECT SUM(system_failed_mn) / SUM(total_volume_mn) * 100 FROM bank_details WHERE year = '2025')
    - (SELECT SUM(system_failed_mn) / SUM(total_volume_mn) * 100 FROM bank_details WHERE year = '2022'),
    SUM(y2025.share_of_payments * (y2025.system_fail_pct - y2022.system_fail_pct))
FROM bank_yearly y2022 JOIN bank_yearly y2025 ON y2025.bank = y2022.bank
WHERE y2022.year = '2022' AND y2025.year = '2025';

INSERT INTO why_split
SELECT 2, 'Decline %, 2022 → 2025',
    (SELECT SUM(user_failed_mn) / SUM(total_volume_mn) * 100 FROM bank_details WHERE year = '2025')
    - (SELECT SUM(user_failed_mn) / SUM(total_volume_mn) * 100 FROM bank_details WHERE year = '2022'),
    SUM(y2025.share_of_payments * (y2025.user_fail_pct - y2022.user_fail_pct))
FROM bank_yearly y2022 JOIN bank_yearly y2025 ON y2025.bank = y2022.bank
WHERE y2022.year = '2022' AND y2025.year = '2025';

INSERT INTO why_split
SELECT 3, 'Decline %, 2025 → 2026',
    (SELECT SUM(user_failed_mn) / SUM(total_volume_mn) * 100 FROM bank_details WHERE year = '2026')
    - (SELECT SUM(user_failed_mn) / SUM(total_volume_mn) * 100 FROM bank_details WHERE year = '2025'),
    SUM(y2026.share_of_payments * (y2026.user_fail_pct - y2025.user_fail_pct))
FROM bank_yearly y2025 JOIN bank_yearly y2026 ON y2026.bank = y2025.bank
WHERE y2025.year = '2025' AND y2026.year = '2026';

\pset format csv

-- one row per bank per month, with all the extra columns
\o powerbi/data/bank_details.csv
SELECT * FROM bank_details
ORDER BY month, bank;

-- dated NPCI / RBI events (made in 05_q3_events_timeline.sql)
\o powerbi/data/events.csv
SELECT * FROM events
ORDER BY month;

-- page 2: the why split (rate vs mix)
\o powerbi/data/why_split.csv
SELECT step, change,
    ROUND(from_banks_themselves, 2) AS from_banks_themselves,
    ROUND(total_change - from_banks_themselves, 2) AS from_payments_moving,
    ROUND(total_change, 2) AS total_change
FROM why_split
ORDER BY step;

-- page 4: system failures and checkout (P2M) payments hit, per year (same as 08_q6, an estimate)
\o powerbi/data/cost_by_year.csv
SELECT b.year, b.year_label,
    ROUND(SUM(b.system_failed_mn)) AS system_failed_mn,
    ROUND(SUM(b.system_failed_mn * p.p2m_share_pct / 100)) AS checkout_payments_hit_mn
FROM bank_details b
JOIN p2p_p2m_monthly p ON p.month = b.month
GROUP BY b.year, b.year_label
ORDER BY b.year;

-- page 4: each bank, last 12 months. avoidable = failed payments above the 1% target (0 if already within)
-- avg_payment_rs = each bank's Rs value / approved payments over the same 12 months (x 10 gives Rs per payment).
-- The small query in brackets works out that average per bank first; LEFT JOIN keeps banks with no value row (blank).
\o powerbi/data/bank_last_12_months.csv
SELECT b.bank, b.bank_group,
    ROUND(SUM(b.total_volume_mn), 2) AS payments_mn,
    ROUND(SUM(b.system_failed_mn), 3) AS system_failed_mn,
    ROUND(GREATEST(SUM(b.system_failed_mn) - SUM(b.total_volume_mn) * 0.01, 0), 3) AS avoidable_at_1pct_mn,
    v.avg_payment_rs
FROM bank_details b
LEFT JOIN (
    SELECT bank, ROUND(SUM(value_cr) / SUM(approved_volume_mn) * 10) AS avg_payment_rs
    FROM bank_value_monthly
    WHERE month >= '2025-10'
    GROUP BY bank
) v ON v.bank = b.bank
WHERE b.month >= '2025-10'
GROUP BY b.bank, b.bank_group, v.avg_payment_rs;

\o
