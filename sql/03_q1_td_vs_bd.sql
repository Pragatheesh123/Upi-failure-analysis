-- QUESTION 1: How have failures moved from the system (TD) to the user (BD) since 2021,
-- overall and by bank group?
-- Percentages are volume-weighted: all failed payments / all payments, never an average of percentages.
-- Note: 2021 has only Aug-Dec (provisional), 2026 only Jan-Sep. See the "months" column.

-- Part A: all banks together, per year
SELECT
    LEFT(month, 4)                                                AS year,
    COUNT(DISTINCT month)                                         AS months,
    ROUND(SUM(total_volume_mn))                                   AS payments_mn,
    ROUND(100 * SUM(td_failed_mn) / SUM(total_volume_mn), 2)      AS td_pct,   -- system failures
    ROUND(100 * SUM(bd_failed_mn) / SUM(total_volume_mn), 2)      AS bd_pct,   -- user failures
    ROUND(SUM(td_failed_mn) / COUNT(DISTINCT month), 1)           AS td_failed_mn_per_month,
    ROUND(SUM(bd_failed_mn) / COUNT(DISTINCT month), 1)           AS bd_failed_mn_per_month
FROM bank_monthly_calc
GROUP BY LEFT(month, 4)
ORDER BY year;


-- Part B: per bank group, per year
SELECT
    bank_group,
    LEFT(month, 4)                                                AS year,
    ROUND(1.0 * COUNT(*) / COUNT(DISTINCT month), 1)              AS banks_per_month,   -- how many banks in the group
    ROUND(100 * SUM(td_failed_mn) / SUM(total_volume_mn), 2)      AS td_pct,
    ROUND(100 * SUM(bd_failed_mn) / SUM(total_volume_mn), 2)      AS bd_pct
FROM bank_monthly_calc
GROUP BY bank_group, LEFT(month, 4)
ORDER BY bank_group, year;
