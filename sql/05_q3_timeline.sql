-- Q3: do the changes line up with dated NPCI / RBI events?
-- events table: add more rows as we find dated sources

DROP TABLE IF EXISTS events;
CREATE TABLE events (
    month TEXT,
    event TEXT,
    source TEXT
);
INSERT INTO events VALUES
('2022-06', 'NPCI targets for every bank: TD below 1%, BD below 5%', 'NPCI circular OC 149A, June 2022'),
('2024-01', 'RBI stops Paytm Payments Bank taking new deposits (from Mar 2024)', 'RBI press release, 31 Jan 2024'),
('2024-03', 'Last month Paytm Payments Bank is in the top 50 data', 'our data: bank_monthly');

-- all banks, month by month, with the events next to it
SELECT c.month,
    ROUND(SUM(c.td_failed_mn) / SUM(c.total_volume_mn) * 100, 2) AS td_pct,
    ROUND(SUM(c.bd_failed_mn) / SUM(c.total_volume_mn) * 100, 2) AS bd_pct,
    e.event
FROM bank_monthly_calc c
LEFT JOIN events e ON e.month = c.month
GROUP BY c.month, e.event
ORDER BY c.month;

-- 6 months before vs 6 months after the NPCI targets (Jun 2022)
SELECT
    CASE WHEN month < '2022-06' THEN 'before' ELSE 'after' END AS period,
    ROUND(SUM(td_failed_mn) / SUM(total_volume_mn) * 100, 2) AS td_pct,
    ROUND(SUM(bd_failed_mn) / SUM(total_volume_mn) * 100, 2) AS bd_pct
FROM bank_monthly_calc
WHERE month BETWEEN '2021-12' AND '2022-11'
GROUP BY period
ORDER BY period DESC;
