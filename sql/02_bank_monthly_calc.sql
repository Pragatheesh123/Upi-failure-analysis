-- Adds the calculated columns to the bank table, as a view called bank_monthly_calc.
-- (A view is a saved query: it works like a table, and is always up to date.)
-- All later questions read from this view.

DROP VIEW IF EXISTS bank_monthly_calc;
CREATE VIEW bank_monthly_calc AS

-- Step 1: turn percentages into numbers of payments (in millions)
WITH counts AS (
    SELECT
        *,
        total_volume_mn * approved_pct / 100  AS approved_mn,
        total_volume_mn * bd_pct / 100        AS bd_failed_mn,   -- failed because of the user
        total_volume_mn * td_pct / 100        AS td_failed_mn,   -- failed because of the system
        RIGHT(month, 2) IN ('10', '11')       AS is_festival_month,
        td_pct > 1.0                          AS above_npci_target,  -- NPCI wants TD below 1%
        -- Group for comparing bank types: very small types go together in "Others"
        CASE
            WHEN bank_type IN ('Co-operative', 'Payment company (PPI)', 'Credit card issuer') THEN 'Others'
            ELSE bank_type
        END                                   AS bank_group
    FROM bank_monthly
),

-- Step 2: average payment in Rs, from the second NPCI table.
-- Joined only when both tables agree on the number of approved payments (within 2%),
-- because a few months in that table have banks swapped or listed twice.
with_value AS (
    SELECT
        c.*,
        v.value_cr * 10 / v.approved_volume_mn  AS avg_payment_value_inr   -- 1 crore = 10 million
    FROM counts AS c
    LEFT JOIN bank_value_monthly AS v
        ON  v.month = c.month
        AND v.bank = c.bank
        AND ABS(v.approved_volume_mn / c.approved_mn - 1) <= 0.02
)

-- Step 3: value of the payments that failed because of the system, in Rs crore
SELECT
    *,
    td_failed_mn * avg_payment_value_inr / 10  AS td_failed_value_cr
FROM with_value;

-- Quick look
SELECT COUNT(*) AS rows, COUNT(avg_payment_value_inr) AS rows_with_value FROM bank_monthly_calc;
