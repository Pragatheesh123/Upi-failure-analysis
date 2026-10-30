-- Q3: Do the changes line up with dated NPCI / RBI events?
-- We keep the events in a small table. Add more rows as we find dated sources.

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

-- every month: fail % for all banks, with the event (if any) next to it
SELECT b.month,
    ROUND(SUM(b.system_failed_mn) / SUM(b.total_volume_mn) * 100, 2) AS system_fail_pct,
    ROUND(SUM(b.user_failed_mn) / SUM(b.total_volume_mn) * 100, 2) AS user_fail_pct,
    events.event
FROM bank_details b
LEFT JOIN events ON events.month = b.month
GROUP BY b.month, events.event
ORDER BY b.month;

-- 6 months before vs 6 months after the NPCI targets (June 2022)
SELECT
    CASE WHEN month < '2022-06' THEN '1 before' ELSE '2 after' END AS period,
    ROUND(SUM(system_failed_mn) / SUM(total_volume_mn) * 100, 2) AS system_fail_pct,
    ROUND(SUM(user_failed_mn) / SUM(total_volume_mn) * 100, 2) AS user_fail_pct
FROM bank_details
WHERE month BETWEEN '2021-12' AND '2022-11'
GROUP BY period
ORDER BY period;
