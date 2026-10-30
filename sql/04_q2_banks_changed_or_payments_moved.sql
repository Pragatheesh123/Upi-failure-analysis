-- Q2: When the overall fail % changed, was it because
--   (a) banks themselves got better or worse, or
--   (b) payments moved to other banks (some banks grew, some left the top 50)?
-- Step 1 finds (a). Then (b) = total change (from Q1) - (a).
-- (a) = for each bank in both years: its share of payments x how much its fail % changed, added up

-- System failures, 2022 -> 2025 (total change from Q1: 1.45 -> 0.40 = -1.05)
SELECT ROUND(SUM(y2025.share_of_payments * (y2025.system_fail_pct - y2022.system_fail_pct)), 2) AS change_from_banks_themselves
FROM bank_yearly y2022
JOIN bank_yearly y2025 ON y2025.bank = y2022.bank
WHERE y2022.year = '2022' AND y2025.year = '2025';

-- User failures, 2022 -> 2025 (total change from Q1: 6.71 -> 7.76 = +1.05)
SELECT ROUND(SUM(y2025.share_of_payments * (y2025.user_fail_pct - y2022.user_fail_pct)), 2) AS change_from_banks_themselves
FROM bank_yearly y2022
JOIN bank_yearly y2025 ON y2025.bank = y2022.bank
WHERE y2022.year = '2022' AND y2025.year = '2025';

-- User failures, 2025 -> 2026 (total change from Q1: 7.76 -> 10.08 = +2.32)
SELECT ROUND(SUM(y2026.share_of_payments * (y2026.user_fail_pct - y2025.user_fail_pct)), 2) AS change_from_banks_themselves
FROM bank_yearly y2025
JOIN bank_yearly y2026 ON y2026.bank = y2025.bank
WHERE y2025.year = '2025' AND y2026.year = '2026';

-- Which banks grew or shrank, 2022 -> 2025 (share = part of all payments)
SELECT y2022.bank, y2022.bank_group,
    ROUND(y2022.share_of_payments * 100, 1) AS share_2022_pct,
    ROUND(y2025.share_of_payments * 100, 1) AS share_2025_pct,
    ROUND(y2022.user_fail_pct, 2) AS user_fail_2022,
    ROUND(y2025.user_fail_pct, 2) AS user_fail_2025
FROM bank_yearly y2022
JOIN bank_yearly y2025 ON y2025.bank = y2022.bank
WHERE y2022.year = '2022' AND y2025.year = '2025'
ORDER BY y2025.share_of_payments - y2022.share_of_payments DESC
LIMIT 10;

-- Banks in 2022 that are gone by 2025 (e.g. Paytm Payments Bank)
SELECT bank, bank_group,
    ROUND(share_of_payments * 100, 1) AS share_2022_pct,
    ROUND(user_fail_pct, 2) AS user_fail_2022
FROM bank_yearly
WHERE year = '2022'
  AND bank NOT IN (SELECT bank FROM bank_yearly WHERE year = '2025')
ORDER BY share_of_payments DESC;
