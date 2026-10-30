-- Q1: Have failures moved from the system side to the user side?
-- fail % = all failed payments / all payments x 100
-- (2021 has only Aug-Dec, 2026 only Jan-Sep)

-- all banks together, per year
SELECT year,
    ROUND(SUM(system_failed_mn) / SUM(total_volume_mn) * 100, 2) AS system_fail_pct,
    ROUND(SUM(user_failed_mn) / SUM(total_volume_mn) * 100, 2) AS user_fail_pct
FROM bank_details
GROUP BY year
ORDER BY year;

-- each bank group, per year
SELECT bank_group, year,
    COUNT(DISTINCT bank) AS banks,
    ROUND(SUM(system_failed_mn) / SUM(total_volume_mn) * 100, 2) AS system_fail_pct,
    ROUND(SUM(user_failed_mn) / SUM(total_volume_mn) * 100, 2) AS user_fail_pct
FROM bank_details
GROUP BY bank_group, year
ORDER BY bank_group, year;
