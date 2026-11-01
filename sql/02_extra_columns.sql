-- Adds extra columns to the bank table. Every question file uses these.
-- TD = system failure (bank or NPCI side)
-- BD = decline: a wrong PIN, low balance, or a limit set by the bank (NPCI calls it "business decline").
--      The column is still called user_failed_mn, but some declines are caused by the bank (NPCI OC 149).

DROP VIEW IF EXISTS bank_details CASCADE;
DROP VIEW IF EXISTS year_totals CASCADE;

-- bank_details: one row per bank per month, with extra columns
CREATE VIEW bank_details AS
SELECT *,
    LEFT(month, 4) AS year,
    total_volume_mn * approved_pct / 100 AS approved_mn,     -- payments that went through (millions)
    total_volume_mn * bd_pct / 100 AS user_failed_mn,        -- payments declined (wrong PIN, low balance, bank limit)
    total_volume_mn * td_pct / 100 AS system_failed_mn,      -- payments that failed because of the system
    RIGHT(month, 2) IN ('10', '11') AS is_festival_month,    -- October or November
    td_pct > 1 AS above_npci_target,                         -- NPCI wants TD below 1%
    CASE WHEN bank_type IN ('Co-operative', 'Payment company (PPI)', 'Credit card issuer') THEN 'Others'
         ELSE bank_type END AS bank_group,                   -- small bank types joined into "Others"
    CASE WHEN bank_type = 'Gramin' THEN 'Gramin banks'
         ELSE 'All other banks' END AS gramin_or_other,      -- for the Gramin vs everyone else line
    CASE WHEN LEFT(month, 4) = '2021' THEN '2021 (Aug-Dec)'
         WHEN LEFT(month, 4) = '2026' THEN '2026 (Jan-Sep)'
         ELSE LEFT(month, 4) END AS year_label               -- partial years say which months they cover
FROM bank_monthly;

-- year_totals: all payments in each year (all banks added up)
CREATE VIEW year_totals AS
SELECT year, SUM(total_volume_mn) AS all_payments_mn
FROM bank_details
GROUP BY year;

-- bank_yearly: one row per bank per year
CREATE VIEW bank_yearly AS
SELECT b.bank, b.bank_group, b.year,
    SUM(b.total_volume_mn) AS payments_mn,
    SUM(b.system_failed_mn) / SUM(b.total_volume_mn) * 100 AS system_fail_pct,
    SUM(b.user_failed_mn) / SUM(b.total_volume_mn) * 100 AS user_fail_pct,
    SUM(b.total_volume_mn) / t.all_payments_mn AS share_of_payments   -- e.g. 0.25 = 25% of all payments
FROM bank_details b
JOIN year_totals t ON t.year = b.year
GROUP BY b.bank, b.bank_group, b.year, t.all_payments_mn;
