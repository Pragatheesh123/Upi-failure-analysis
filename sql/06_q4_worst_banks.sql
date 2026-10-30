-- Q4: Which banks still have the most system failures? Steady problem or a few bad months?
-- "last 12 months" = Oct 2025 to Sep 2026

-- 10 worst banks in the last 12 months
-- months_above_1pct: near 12 = a steady problem, small = only a few bad months
SELECT bank, bank_group,
    COUNT(*) AS months_in_top_50,
    ROUND(SUM(system_failed_mn) / SUM(total_volume_mn) * 100, 2) AS system_fail_pct,
    SUM(CASE WHEN above_npci_target THEN 1 ELSE 0 END) AS months_above_1pct,
    MAX(td_pct) AS worst_month_pct
FROM bank_details
WHERE month >= '2025-10'
GROUP BY bank, bank_group
ORDER BY system_fail_pct DESC
LIMIT 10;

-- bank groups in the last 12 months
SELECT bank_group,
    COUNT(DISTINCT bank) AS banks,
    ROUND(SUM(system_failed_mn) / SUM(total_volume_mn) * 100, 2) AS system_fail_pct
FROM bank_details
WHERE month >= '2025-10'
GROUP BY bank_group
ORDER BY system_fail_pct DESC;

-- is each bank getting better? 2025 vs 2026 (negative change = better)
SELECT y2025.bank, y2025.bank_group,
    ROUND(y2025.system_fail_pct, 2) AS fail_pct_2025,
    ROUND(y2026.system_fail_pct, 2) AS fail_pct_2026,
    ROUND(y2026.system_fail_pct - y2025.system_fail_pct, 2) AS change
FROM bank_yearly y2025
JOIN bank_yearly y2026 ON y2026.bank = y2025.bank
WHERE y2025.year = '2025' AND y2026.year = '2026'
ORDER BY fail_pct_2026 DESC;
