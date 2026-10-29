-- Adds calculated columns to the bank table. Saved as a view called bank_monthly_calc.
-- (A view is a saved query. You use it like a table.)

DROP VIEW IF EXISTS bank_monthly_calc;
CREATE VIEW bank_monthly_calc AS
SELECT
    b.*,
    LEFT(b.month, 4)                          AS year,

    -- Number of payments, in millions = total payments x % / 100
    b.total_volume_mn * b.approved_pct / 100  AS approved_mn,
    b.total_volume_mn * b.bd_pct / 100        AS bd_failed_mn,   -- failed because of the user
    b.total_volume_mn * b.td_pct / 100        AS td_failed_mn,   -- failed because of the system

    RIGHT(b.month, 2) IN ('10', '11')         AS is_festival_month,   -- October or November
    b.td_pct > 1                              AS above_npci_target,   -- NPCI wants TD below 1%

    -- Small bank types go together in one group called Others
    CASE
        WHEN b.bank_type IN ('Co-operative', 'Payment company (PPI)', 'Credit card issuer') THEN 'Others'
        ELSE b.bank_type
    END                                       AS bank_group,

    -- Average payment in Rs (1 crore = 10 million)
    v.value_cr * 10 / v.approved_volume_mn    AS avg_payment_value_inr,
    -- Rs crore lost to system failures = system-failed payments x average payment
    b.total_volume_mn * b.td_pct / 100 * v.value_cr / v.approved_volume_mn  AS td_failed_value_cr

FROM bank_monthly AS b
LEFT JOIN bank_value_monthly AS v
    ON  v.month = b.month
    AND v.bank = b.bank
    -- only when both NPCI tables agree on the approved payments (within 2%)
    AND v.approved_volume_mn BETWEEN 0.98 * (b.total_volume_mn * b.approved_pct / 100)
                                 AND 1.02 * (b.total_volume_mn * b.approved_pct / 100);
