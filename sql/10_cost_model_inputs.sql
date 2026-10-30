-- Numbers for the Excel cost model. Each query is saved as a CSV file in excel/cost_model_inputs/.
-- Python step 4 puts them together into excel/upi_cost_model.xlsx.
-- Run with psql (like 01), because \o (save to a file) only works in psql:
-- & "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d upi_failure -f sql/10_cost_model_inputs.sql

\pset format csv

-- 1) payments and system failures, per year (2021 left out: no Rs values that year)
\o excel/cost_model_inputs/yearly_failures.csv
SELECT year,
    ROUND(SUM(total_volume_mn), 1) AS payments_mn,
    ROUND(SUM(system_failed_mn), 2) AS system_failed_mn
FROM bank_details
WHERE year >= '2022'
GROUP BY year
ORDER BY year;

-- 2) average payment size in Rs, per year
-- value_cr is in Rs crore, approved_volume_mn in millions, so x 10 gives Rs per payment
\o excel/cost_model_inputs/yearly_avg_payment.csv
SELECT LEFT(month, 4) AS year,
    ROUND(SUM(value_cr) / SUM(approved_volume_mn) * 10) AS avg_payment_rs
FROM bank_value_monthly
GROUP BY LEFT(month, 4)
ORDER BY year;

-- 3) share of payments that are shop / checkout payments (P2M), per year
\o excel/cost_model_inputs/yearly_checkout_share.csv
SELECT LEFT(month, 4) AS year,
    ROUND(SUM(p2m_volume_mn) / SUM(total_volume_mn) * 100, 1) AS checkout_share_pct
FROM p2p_p2m_monthly
GROUP BY LEFT(month, 4)
ORDER BY year;

-- 4) payments and system failures per bank, last 12 months (Oct 2025 to Sep 2026)
\o excel/cost_model_inputs/bank_failures.csv
SELECT bank, bank_group,
    ROUND(SUM(total_volume_mn), 2) AS payments_mn,
    ROUND(SUM(system_failed_mn), 3) AS system_failed_mn
FROM bank_details
WHERE month >= '2025-10'
GROUP BY bank, bank_group
ORDER BY SUM(system_failed_mn) / SUM(total_volume_mn) DESC;

-- 5) average payment size per bank, last 12 months
\o excel/cost_model_inputs/bank_avg_payment.csv
SELECT bank,
    ROUND(SUM(value_cr) / SUM(approved_volume_mn) * 10) AS avg_payment_rs
FROM bank_value_monthly
WHERE month >= '2025-10'
GROUP BY bank;

\o
