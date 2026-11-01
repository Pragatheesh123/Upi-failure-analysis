-- Q3: Do the changes line up with dated NPCI / RBI events?
-- We keep the events in a small table. Add more rows as we find dated sources.

DROP TABLE IF EXISTS events;
CREATE TABLE events (
    month TEXT,
    event TEXT,
    source TEXT
);
INSERT INTO events VALUES
('2022-05', 'NPCI targets (advised by RBI): TD below 1%, BD below 5%; banks above 10% BD to run customer awareness campaigns', 'NPCI OC 149 (13 May 2022) and addendum OC 149A (15 Jun 2022)'),
('2024-01', 'RBI stops Paytm Payments Bank taking new deposits (from Mar 2024)', 'RBI press release, 31 Jan 2024'),
('2024-03', 'Last month Paytm Payments Bank is in the top 50 data', 'our data: bank_monthly'),
('2025-03', 'NPCI says some failures came from year-end load at banks', 'Business Standard, 1 Apr 2025'),
('2025-04', 'Big UPI outage (12 Apr); NPCI circular 26 Apr: max 3 status checks, stop on known error codes', 'Upstox / Business Standard, 29 Apr 2025'),
('2025-06', 'NPCI cuts response time from 30 to 10-15 seconds (from 16 Jun)', 'Tribune India, 16 Jun 2025'),
('2025-08', 'NPCI API rules start: 50 balance checks a day per app, AutoPay only outside peak hours', 'NPCI guidelines 21 May 2025, via SCC Online, 30 Jul 2025'),
('2025-10', 'NPCI ends P2P collect requests (from 1 Oct)', 'NPCI circular 29 Jul 2025, via Outlook Money'),
('2026-04', 'RBI rules start: two-factor check for all digital payments (from 1 Apr)', 'RBI Authentication Directions, 25 Sep 2025');

-- events are dates only. Lining up with a change does NOT prove the event caused it.

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

-- May 2025: user failures fell 1.6 points in one month. Did it happen at most banks, or only a few?
-- (if nearly every bank fell in the same month, it looks like a system-wide change, not banks improving one by one)
SELECT COUNT(*) AS banks_in_both_months,
    SUM(CASE WHEN may.bd_pct < apr.bd_pct THEN 1 ELSE 0 END) AS banks_where_user_fail_fell
FROM bank_details apr
JOIN bank_details may ON may.bank = apr.bank
WHERE apr.month = '2025-04' AND may.month = '2025-05';
