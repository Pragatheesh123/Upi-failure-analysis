-- QUESTION 1: Have failures moved from the system (TD) to the user (BD)?
-- % = all failed payments / all payments x 100 (not an average of the banks' %)
-- 2021 has only Aug-Dec, 2026 only Jan-Sep.

-- All banks, per year
SELECT
    year,
    COUNT(DISTINCT month)                                    AS months,
    ROUND(100 * SUM(td_failed_mn) / SUM(total_volume_mn), 2) AS td_pct,
    ROUND(100 * SUM(bd_failed_mn) / SUM(total_volume_mn), 2) AS bd_pct
FROM bank_monthly_calc
GROUP BY year
ORDER BY year;

-- Each bank group, per year
SELECT
    bank_group,
    year,
    COUNT(DISTINCT bank)                                     AS banks,
    ROUND(100 * SUM(td_failed_mn) / SUM(total_volume_mn), 2) AS td_pct,
    ROUND(100 * SUM(bd_failed_mn) / SUM(total_volume_mn), 2) AS bd_pct
FROM bank_monthly_calc
GROUP BY bank_group, year
ORDER BY bank_group, year;
