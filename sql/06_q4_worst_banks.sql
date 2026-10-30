-- Q4: which banks still have the highest TD, and is it steady or sudden spikes?
-- last 12 months = Oct 2025 to Sep 2026

-- top 10 banks by TD in the last 12 months
-- months_above_1pct close to 12 = steady problem, small = a few spikes
SELECT bank, bank_group,
    COUNT(*) AS months,
    ROUND(SUM(td_failed_mn) / SUM(total_volume_mn) * 100, 2) AS td_pct,
    SUM(CASE WHEN above_npci_target THEN 1 ELSE 0 END) AS months_above_1pct,
    MAX(td_pct) AS worst_month,
    RANK() OVER (ORDER BY SUM(td_failed_mn) / SUM(total_volume_mn) DESC) AS td_rank
FROM bank_monthly_calc
WHERE month >= '2025-10'
GROUP BY bank, bank_group
ORDER BY td_rank
LIMIT 10;

-- same for bank groups
SELECT bank_group,
    COUNT(DISTINCT bank) AS banks,
    ROUND(SUM(td_failed_mn) / SUM(total_volume_mn) * 100, 2) AS td_pct
FROM bank_monthly_calc
WHERE month >= '2025-10'
GROUP BY bank_group
ORDER BY td_pct DESC;

-- is each bank improving? TD per year and the change from last year
SELECT bank, year,
    ROUND(td_pct, 2) AS td_pct,
    ROUND(td_pct - LAG(td_pct) OVER (PARTITION BY bank ORDER BY year), 2) AS change_vs_last_year
FROM bank_year
ORDER BY bank, year;
