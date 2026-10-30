-- Q7 (extra): is TD higher or lower in festival months (Oct-Nov)?
-- TD fell every year, so compare festival months with the other months of the same year
-- (2026 has no Oct-Nov yet). The Mann-Whitney test runs in Python on the first query.

-- TD for every month, with the festival flag
SELECT month, year, is_festival_month,
    ROUND(SUM(td_failed_mn) / SUM(total_volume_mn) * 100, 3) AS td_pct
FROM bank_monthly_calc
GROUP BY month, year, is_festival_month
ORDER BY month;

-- festival vs other months, each year
SELECT year,
    ROUND(SUM(CASE WHEN is_festival_month THEN td_failed_mn END) / SUM(CASE WHEN is_festival_month THEN total_volume_mn END) * 100, 2) AS festival_td,
    ROUND(SUM(CASE WHEN NOT is_festival_month THEN td_failed_mn END) / SUM(CASE WHEN NOT is_festival_month THEN total_volume_mn END) * 100, 2) AS other_months_td
FROM bank_monthly_calc
GROUP BY year
ORDER BY year;
