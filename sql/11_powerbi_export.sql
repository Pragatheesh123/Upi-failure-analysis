-- Saves the tables Power BI needs as CSV files in powerbi/data/.
-- Power BI then only adds things up; every calculated column comes from 02_extra_columns.sql.
-- Run with psql (like 01 and 10):
-- & "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d upi_failure -f sql/11_powerbi_export.sql

\pset format csv

-- one row per bank per month, with all the extra columns
\o powerbi/data/bank_details.csv
SELECT * FROM bank_details
ORDER BY month, bank;

-- dated NPCI / RBI events (made in 05_q3_events_timeline.sql)
\o powerbi/data/events.csv
SELECT * FROM events
ORDER BY month;

\o
