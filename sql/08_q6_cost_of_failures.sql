-- Q6: What did system failures cost? (both answers are estimates)

-- 1) Value of system-failed payments in Rs crore, per year
-- value = failed payments x the bank's average payment size
-- average payment size = value_cr / approved_volume_mn from NPCI's second table (bank_value_monthly)
-- we only use it when both NPCI tables agree on the bank's approved payments (within 2%)
-- failed_with_value_mn = failed payments that found a matching row (2021 has none)
SELECT b.year,
    ROUND(SUM(b.system_failed_mn)) AS system_failed_mn,
    ROUND(SUM(CASE WHEN v.bank IS NOT NULL THEN b.system_failed_mn END)) AS failed_with_value_mn,
    ROUND(SUM(b.system_failed_mn * v.value_cr / v.approved_volume_mn)) AS failed_value_cr
FROM bank_details b
LEFT JOIN bank_value_monthly v
    ON v.month = b.month
    AND v.bank = b.bank
    AND v.approved_volume_mn BETWEEN b.approved_mn * 0.98 AND b.approved_mn * 1.02
GROUP BY b.year
ORDER BY b.year;

-- 2) Shop / checkout payments (P2M) hit by system failures, per year
-- estimate: failed payments x that month's share of shop payments
SELECT b.year,
    ROUND(SUM(b.system_failed_mn)) AS system_failed_mn,
    ROUND(SUM(b.system_failed_mn * p.p2m_share_pct / 100)) AS checkout_payments_hit_mn
FROM bank_details b
JOIN p2p_p2m_monthly p ON p.month = b.month
GROUP BY b.year
ORDER BY b.year;
