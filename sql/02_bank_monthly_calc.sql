-- bank table + extra columns used by all the questions
DROP VIEW IF EXISTS bank_monthly_calc CASCADE;

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

-- one row per bank per year, with its share of all payments that year
CREATE VIEW bank_year AS
SELECT bank, bank_group, year,
    SUM(total_volume_mn) AS payments_mn,
    SUM(td_failed_mn) / SUM(total_volume_mn) * 100 AS td_pct,
    SUM(bd_failed_mn) / SUM(total_volume_mn) * 100 AS bd_pct,
    SUM(total_volume_mn) / (SELECT SUM(total_volume_mn) FROM bank_monthly_calc t WHERE t.year = c.year) AS share
FROM bank_monthly_calc c
GROUP BY bank, bank_group, year;
