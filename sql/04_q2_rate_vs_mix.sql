-- Q2: did the overall % change because banks got better/worse (rate),
-- or because payments moved to other banks (mix)?
-- overall % = sum of (bank's share x bank's %), so each bank's part of the change is
--   share_new x pct_new - share_old x pct_old
-- rate effect = share_new x (pct_new - pct_old)   (only banks in both years)
-- mix effect  = the rest (share moves, banks joining or leaving the top 50)

-- each bank's share and % in 2022, 2025 and 2026 side by side
DROP VIEW IF EXISTS bank_3_years;
CREATE VIEW bank_3_years AS
SELECT bank, bank_group,
    MAX(CASE WHEN year = '2022' THEN share END) AS share_2022,
    MAX(CASE WHEN year = '2025' THEN share END) AS share_2025,
    MAX(CASE WHEN year = '2026' THEN share END) AS share_2026,
    MAX(CASE WHEN year = '2022' THEN td_pct END) AS td_2022,
    MAX(CASE WHEN year = '2025' THEN td_pct END) AS td_2025,
    MAX(CASE WHEN year = '2022' THEN bd_pct END) AS bd_2022,
    MAX(CASE WHEN year = '2025' THEN bd_pct END) AS bd_2025,
    MAX(CASE WHEN year = '2026' THEN bd_pct END) AS bd_2026
FROM bank_year
GROUP BY bank, bank_group;

-- TD 2022 -> 2025
SELECT
    ROUND(SUM(COALESCE(share_2025 * td_2025, 0) - COALESCE(share_2022 * td_2022, 0)), 2) AS total_change,
    ROUND(SUM(COALESCE(share_2025 * (td_2025 - td_2022), 0)), 2) AS rate_effect
FROM bank_3_years;

-- BD 2022 -> 2025
SELECT
    ROUND(SUM(COALESCE(share_2025 * bd_2025, 0) - COALESCE(share_2022 * bd_2022, 0)), 2) AS total_change,
    ROUND(SUM(COALESCE(share_2025 * (bd_2025 - bd_2022), 0)), 2) AS rate_effect
FROM bank_3_years;

-- BD 2025 -> 2026
SELECT
    ROUND(SUM(COALESCE(share_2026 * bd_2026, 0) - COALESCE(share_2025 * bd_2025, 0)), 2) AS total_change,
    ROUND(SUM(COALESCE(share_2026 * (bd_2026 - bd_2025), 0)), 2) AS rate_effect
FROM bank_3_years;
-- mix effect = total_change - rate_effect

-- banks behind the BD change 2022 -> 2025 (biggest first)
SELECT bank, bank_group,
    ROUND(share_2022 * 100, 1) AS share_2022_pct,
    ROUND(share_2025 * 100, 1) AS share_2025_pct,
    ROUND(bd_2022, 2) AS bd_2022,
    ROUND(bd_2025, 2) AS bd_2025,
    ROUND(COALESCE(share_2025 * bd_2025, 0) - COALESCE(share_2022 * bd_2022, 0), 3) AS part_of_change,
    ROUND(COALESCE(share_2025 * (bd_2025 - bd_2022), 0), 3) AS rate_part
FROM bank_3_years
ORDER BY ABS(COALESCE(share_2025 * bd_2025, 0) - COALESCE(share_2022 * bd_2022, 0)) DESC
LIMIT 10;
