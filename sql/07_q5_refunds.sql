-- Q5: when money is taken but the payment fails, how often does the refund work?
-- refunds that worked = debit_reversal_count_mn x debit_reversal_success_pct / 100
-- rows where NPCI gave no refund numbers are left out

-- all banks, per year
SELECT year,
    ROUND(SUM(debit_reversal_count_mn)) AS refunds_needed_mn,
    ROUND(SUM(debit_reversal_count_mn * debit_reversal_success_pct / 100) / SUM(debit_reversal_count_mn) * 100, 2) AS refund_success_pct
FROM bank_monthly_calc
WHERE debit_reversal_success_pct IS NOT NULL
GROUP BY year
ORDER BY year;

-- bank groups, last 12 months
SELECT bank_group,
    ROUND(SUM(debit_reversal_count_mn * debit_reversal_success_pct / 100) / SUM(debit_reversal_count_mn) * 100, 2) AS refund_success_pct
FROM bank_monthly_calc
WHERE debit_reversal_success_pct IS NOT NULL
  AND month >= '2025-10'
GROUP BY bank_group
ORDER BY refund_success_pct;

-- 10 banks with the worst refund success, last 12 months
SELECT bank, bank_group,
    ROUND(SUM(debit_reversal_count_mn), 2) AS refunds_needed_mn,
    ROUND(SUM(debit_reversal_count_mn * debit_reversal_success_pct / 100) / SUM(debit_reversal_count_mn) * 100, 2) AS refund_success_pct
FROM bank_monthly_calc
WHERE debit_reversal_success_pct IS NOT NULL
  AND month >= '2025-10'
GROUP BY bank, bank_group
HAVING SUM(debit_reversal_count_mn) > 0   -- skip banks with no refunds needed
ORDER BY refund_success_pct
LIMIT 10;
