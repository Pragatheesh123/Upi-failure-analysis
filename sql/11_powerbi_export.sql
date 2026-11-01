-- Saves the tables Power BI needs as CSV files in powerbi/data/.
-- Power BI then only adds things up; every calculated column comes from 02_extra_columns.sql.
-- Run with psql (like 01 and 10):
-- & "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d upi_failure -f sql/11_powerbi_export.sql

-- year_rates: each year's overall % for all banks together (total failed / total payments)
DROP VIEW IF EXISTS year_rates;
CREATE VIEW year_rates AS
SELECT year,
    SUM(system_failed_mn) / SUM(total_volume_mn) * 100 AS system_fail_pct,
    SUM(user_failed_mn) / SUM(total_volume_mn) * 100 AS user_fail_pct
FROM bank_details
GROUP BY year;

-- Page 2 "why" chart: each change split in two (same idea as 04_q2)
-- total_change = new year's % minus old year's %, looked up in year_rates
-- from_banks_themselves = each bank's own change in %, weighted by its share of payments
-- the rest of the change (worked out in the export below) = payments moving between banks
DROP TABLE IF EXISTS why_split;
CREATE TABLE why_split (step INT, change TEXT, total_change NUMERIC, from_banks_themselves NUMERIC);

INSERT INTO why_split
SELECT 1, 'System failure %, 2022 → 2025',
    (SELECT system_fail_pct FROM year_rates WHERE year = '2025') - (SELECT system_fail_pct FROM year_rates WHERE year = '2022'),
    SUM(y2025.share_of_payments * (y2025.system_fail_pct - y2022.system_fail_pct))
FROM bank_yearly y2022 JOIN bank_yearly y2025 ON y2025.bank = y2022.bank
WHERE y2022.year = '2022' AND y2025.year = '2025';

INSERT INTO why_split
SELECT 2, 'Decline %, 2022 → 2025',
    (SELECT user_fail_pct FROM year_rates WHERE year = '2025') - (SELECT user_fail_pct FROM year_rates WHERE year = '2022'),
    SUM(y2025.share_of_payments * (y2025.user_fail_pct - y2022.user_fail_pct))
FROM bank_yearly y2022 JOIN bank_yearly y2025 ON y2025.bank = y2022.bank
WHERE y2022.year = '2022' AND y2025.year = '2025';

INSERT INTO why_split
SELECT 3, 'Decline %, 2025 → 2026',
    (SELECT user_fail_pct FROM year_rates WHERE year = '2026') - (SELECT user_fail_pct FROM year_rates WHERE year = '2025'),
    SUM(y2026.share_of_payments * (y2026.user_fail_pct - y2025.user_fail_pct))
FROM bank_yearly y2025 JOIN bank_yearly y2026 ON y2026.bank = y2025.bank
WHERE y2025.year = '2025' AND y2026.year = '2026';

-- bank_avg_payment_last_12_months: each bank's average payment in Rs, Oct 2025 to Sep 2026
-- value_cr is in Rs crore and approved_volume_mn in millions, so x 10 gives Rs per payment
DROP VIEW IF EXISTS bank_avg_payment_last_12_months;
CREATE VIEW bank_avg_payment_last_12_months AS
SELECT bank, ROUND(SUM(value_cr) / SUM(approved_volume_mn) * 10) AS avg_payment_rs
FROM bank_value_monthly
WHERE month >= '2025-10'
GROUP BY bank;

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

-- page 4: each bank, last 12 months
-- avoidable = failed payments above the 1% target. GREATEST(x, 0) = the bigger of x and 0, so a bank already within the target gets 0
-- LEFT JOIN keeps every bank, even one with no Rs value (its avg_payment_rs stays blank)
\o powerbi/data/bank_last_12_months.csv
SELECT b.bank, b.bank_group,
    ROUND(SUM(b.total_volume_mn), 2) AS payments_mn,
    ROUND(SUM(b.system_failed_mn), 3) AS system_failed_mn,
    ROUND(GREATEST(SUM(b.system_failed_mn) - SUM(b.total_volume_mn) * 0.01, 0), 3) AS avoidable_at_1pct_mn,
    a.avg_payment_rs
FROM bank_details b
LEFT JOIN bank_avg_payment_last_12_months a ON a.bank = b.bank
WHERE b.month >= '2025-10'
GROUP BY b.bank, b.bank_group, a.avg_payment_rs;

\o
