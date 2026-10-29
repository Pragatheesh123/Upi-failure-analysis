-- bank table + extra columns used by all the questions
DROP VIEW IF EXISTS bank_monthly_calc;

CREATE VIEW bank_monthly_calc AS
SELECT *,
    LEFT(month, 4) AS year,
    total_volume_mn * approved_pct / 100 AS approved_mn,
    total_volume_mn * bd_pct / 100 AS bd_failed_mn,
    total_volume_mn * td_pct / 100 AS td_failed_mn,
    RIGHT(month, 2) IN ('10', '11') AS is_festival_month,
    td_pct > 1 AS above_npci_target,
    CASE WHEN bank_type IN ('Co-operative', 'Payment company (PPI)', 'Credit card issuer') THEN 'Others'
         ELSE bank_type END AS bank_group
FROM bank_monthly;
