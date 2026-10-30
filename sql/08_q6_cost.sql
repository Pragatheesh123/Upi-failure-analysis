-- Q6: what did system failures cost? (both numbers are estimates)

-- 1) system-failed payments and their value in Rs crore, per year
-- value = failed payments x the bank's average payment (from the vol & val table)
-- only used when both NPCI tables agree on approved payments (within 2%)
-- coverage_pct = share of failed payments that got a value (2021 has none)
SELECT c.year,
    ROUND(SUM(c.td_failed_mn)) AS system_failed_mn,
    ROUND(SUM(c.td_failed_mn * v.value_cr / v.approved_volume_mn)) AS value_cr_estimate,
    ROUND(SUM(CASE WHEN v.bank IS NOT NULL THEN c.td_failed_mn END) / SUM(c.td_failed_mn) * 100, 1) AS coverage_pct
FROM bank_monthly_calc c
LEFT JOIN bank_value_monthly v
    ON v.month = c.month
    AND v.bank = c.bank
    AND v.approved_volume_mn BETWEEN c.approved_mn * 0.98 AND c.approved_mn * 1.02
GROUP BY c.year
ORDER BY c.year;

-- 2) checkout (shop) payments hit by system failures, per year
-- estimate: assumes failures hit shop payments in the same share as all payments that month
SELECT c.year,
    ROUND(SUM(c.td_failed_mn)) AS system_failed_mn,
    ROUND(SUM(c.td_failed_mn * p.p2m_share_pct / 100)) AS checkout_hit_mn_estimate
FROM bank_monthly_calc c
JOIN p2p_p2m_monthly p ON p.month = c.month
GROUP BY c.year
ORDER BY c.year;
