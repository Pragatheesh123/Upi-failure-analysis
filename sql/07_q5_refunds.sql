-- Q5: When money is taken but the payment fails, how often does the refund work?
-- refunds_needed_mn = debit_reversal_count_mn (money taken, payment failed)
-- refunds that worked = refunds needed x refund success % / 100
-- months where NPCI gave no refund numbers are left out

-- all banks, per year
SELECT year,
    ROUND(SUM(debit_reversal_count_mn)) AS refunds_needed_mn,
    ROUND(SUM(debit_reversal_count_mn * debit_reversal_success_pct / 100) / SUM(debit_reversal_count_mn) * 100, 2) AS refund_success_pct
FROM bank_details
WHERE debit_reversal_success_pct IS NOT NULL
GROUP BY year
ORDER BY year;

-- bank groups, last 12 months (Oct 2025 to Sep 2026)
SELECT bank_group,
    ROUND(SUM(debit_reversal_count_mn * debit_reversal_success_pct / 100) / SUM(debit_reversal_count_mn) * 100, 2) AS refund_success_pct
FROM bank_details
WHERE debit_reversal_success_pct IS NOT NULL
  AND month >= '2025-10'
GROUP BY bank_group
ORDER BY refund_success_pct;

-- 10 banks with the worst refunds, last 12 months
SELECT bank, bank_group,
    ROUND(SUM(debit_reversal_count_mn), 2) AS refunds_needed_mn,
    ROUND(SUM(debit_reversal_count_mn * debit_reversal_success_pct / 100) / SUM(debit_reversal_count_mn) * 100, 2) AS refund_success_pct
FROM bank_details
WHERE debit_reversal_success_pct IS NOT NULL
  AND month >= '2025-10'
GROUP BY bank, bank_group
HAVING SUM(debit_reversal_count_mn) > 0   -- skip banks with no refunds (can't divide by 0)
ORDER BY refund_success_pct
LIMIT 10;
