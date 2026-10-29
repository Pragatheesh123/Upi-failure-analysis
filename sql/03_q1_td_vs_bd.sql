-- Q1: system failures (TD) vs user failures (BD) over the years
-- note: 2021 is only Aug-Dec, 2026 is only Jan-Sep

SELECT year,
    ROUND(SUM(td_failed_mn) / SUM(total_volume_mn) * 100, 2) AS td_pct,
    ROUND(SUM(bd_failed_mn) / SUM(total_volume_mn) * 100, 2) AS bd_pct
FROM bank_monthly_calc
GROUP BY year
ORDER BY year;

-- same thing by bank group
SELECT bank_group, year,
    COUNT(DISTINCT bank) AS banks,
    ROUND(SUM(td_failed_mn) / SUM(total_volume_mn) * 100, 2) AS td_pct,
    ROUND(SUM(bd_failed_mn) / SUM(total_volume_mn) * 100, 2) AS bd_pct
FROM bank_monthly_calc
GROUP BY bank_group, year
ORDER BY bank_group, year;
