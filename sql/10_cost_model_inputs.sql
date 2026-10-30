-- Numbers for the Excel cost model (excel/upi_cost_model.xlsx).
-- Makes 2 small views, then saves them as CSV files. Python step 4 builds the Excel file from them.
-- Run with psql (like 01), not pgAdmin, because of \copy.

-- one row per year (2022 on: 2021 has no Rs values)
-- avg_payment_rs = average Rs size of a system-failed payment (only where the 2 NPCI tables agree, like Q6)
-- checkout_share_pct = share of system-failed payments that were shop payments (P2M), estimate like Q6
DROP VIEW IF EXISTS cost_model_yearly;
CREATE VIEW cost_model_yearly AS
SELECT b.year,
    ROUND(SUM(b.total_volume_mn), 1) AS payments_mn,
    ROUND(SUM(b.system_failed_mn), 2) AS system_failed_mn,
    ROUND(SUM(b.system_failed_mn * v.value_cr / v.approved_volume_mn)
        / SUM(CASE WHEN v.bank IS NOT NULL THEN b.system_failed_mn END) * 10) AS avg_payment_rs,
    ROUND(SUM(b.system_failed_mn * p.p2m_share_pct) / SUM(b.system_failed_mn), 1) AS checkout_share_pct
FROM bank_details b
LEFT JOIN bank_value_monthly v
    ON v.month = b.month
    AND v.bank = b.bank
    AND v.approved_volume_mn BETWEEN b.approved_mn * 0.98 AND b.approved_mn * 1.02
JOIN p2p_p2m_monthly p ON p.month = b.month
WHERE b.year >= '2022'
GROUP BY b.year
ORDER BY b.year;

-- one row per bank, last 12 months (Oct 2025 to Sep 2026)
-- avg_payment_rs is blank when the 2 NPCI tables never agree for that bank
-- NULLIF(x, 0) turns 0 into blank, so a bank with 0 failures gives blank instead of a divide-by-zero error
DROP VIEW IF EXISTS cost_model_banks;
CREATE VIEW cost_model_banks AS
SELECT b.bank, b.bank_group,
    ROUND(SUM(b.total_volume_mn), 2) AS payments_mn,
    ROUND(SUM(b.system_failed_mn), 3) AS system_failed_mn,
    ROUND(SUM(b.system_failed_mn * v.value_cr / v.approved_volume_mn)
        / NULLIF(SUM(CASE WHEN v.bank IS NOT NULL THEN b.system_failed_mn END), 0) * 10) AS avg_payment_rs
FROM bank_details b
LEFT JOIN bank_value_monthly v
    ON v.month = b.month
    AND v.bank = b.bank
    AND v.approved_volume_mn BETWEEN b.approved_mn * 0.98 AND b.approved_mn * 1.02
WHERE b.month >= '2025-10'
GROUP BY b.bank, b.bank_group
ORDER BY SUM(b.system_failed_mn) / SUM(b.total_volume_mn) DESC;

\copy (SELECT * FROM cost_model_yearly) TO 'excel/cost_model_yearly.csv' CSV HEADER
\copy (SELECT * FROM cost_model_banks) TO 'excel/cost_model_banks.csv' CSV HEADER
