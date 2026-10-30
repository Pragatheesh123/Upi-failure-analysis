-- Q7 (extra): Are system failures higher or lower in festival months (Oct-Nov)?
-- Failures fell every year, so we compare festival months with other months of the same year.
-- (2026 has no Oct-Nov yet.) The statistics test (Mann-Whitney) runs in Python on the first result.

-- system fail % for every month
SELECT month, year, is_festival_month,
    ROUND(SUM(system_failed_mn) / SUM(total_volume_mn) * 100, 3) AS system_fail_pct
FROM bank_details
GROUP BY month, year, is_festival_month
ORDER BY month;

-- each year: festival months vs other months
SELECT year, is_festival_month,
    ROUND(SUM(system_failed_mn) / SUM(total_volume_mn) * 100, 2) AS system_fail_pct
FROM bank_details
GROUP BY year, is_festival_month
ORDER BY year, is_festival_month;
