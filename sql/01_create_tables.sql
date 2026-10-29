-- STEP 3: put the 4 clean CSV files into PostgreSQL (database upi_failure)
-- Run from the project folder:
--   & "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d upi_failure -f sql/01_create_tables.sql
-- Running it again deletes the tables and loads them fresh.

-- One row per bank per month (Aug 2021 onwards, top 50 banks)
DROP TABLE IF EXISTS bank_monthly CASCADE;
CREATE TABLE bank_monthly (
    month                       TEXT,      -- '2022-01'
    bank_raw                    TEXT,      -- name as NPCI wrote it
    bank                        TEXT,      -- standard name
    bank_type                   TEXT,      -- Public, Private, Small finance, ...
    rank_in_source              INT,
    total_volume_mn             NUMERIC,   -- payments started, in millions
    approved_pct                NUMERIC,
    bd_pct                      NUMERIC,   -- failed because of the user (wrong PIN, low balance)
    td_pct                      NUMERIC,   -- failed because of the system (bank or NPCI)
    debit_reversal_count_mn     NUMERIC,   -- money taken but payment failed, refunds in millions
    debit_reversal_success_pct  NUMERIC,
    udir_auto_update_sr_pct     NUMERIC,
    udir_refund_sr_pct          NUMERIC,
    source                      TEXT,
    is_name_corrected           BOOLEAN,
    PRIMARY KEY (month, bank)              -- each bank only once per month
);
\copy bank_monthly FROM 'data/clean/upi_bank_monthly.csv' WITH (FORMAT csv, HEADER true)

-- Approved payments and their value per bank per month (a second NPCI table)
DROP TABLE IF EXISTS bank_value_monthly CASCADE;
CREATE TABLE bank_value_monthly (
    month               TEXT,
    bank_raw            TEXT,
    bank                TEXT,
    approved_volume_mn  NUMERIC,
    value_cr            NUMERIC        -- Rs crore
);
\copy bank_value_monthly FROM 'data/clean/upi_bank_value_monthly.csv' WITH (FORMAT csv, HEADER true)

-- One row per UPI app per month (NPCI lists a few apps twice in some months, e.g. Bajaj Finserv Feb 2023, so no key here)
DROP TABLE IF EXISTS app_monthly CASCADE;
CREATE TABLE app_monthly (
    month          TEXT,
    app            TEXT,
    volume_mn      NUMERIC,
    value_cr       NUMERIC,
    app_share_pct  NUMERIC
);
\copy app_monthly FROM 'data/clean/upi_app_monthly.csv' WITH (FORMAT csv, HEADER true)

-- Person-to-person (P2P) vs shop/checkout (P2M) payments, one row per month
DROP TABLE IF EXISTS p2p_p2m_monthly CASCADE;
CREATE TABLE p2p_p2m_monthly (
    month            TEXT PRIMARY KEY,
    p2p_volume_mn    NUMERIC,
    p2p_value_cr     NUMERIC,
    p2m_volume_mn    NUMERIC,
    p2m_value_cr     NUMERIC,
    total_volume_mn  NUMERIC,
    p2m_share_pct    NUMERIC
);
\copy p2p_p2m_monthly FROM 'data/clean/upi_p2p_p2m_monthly.csv' WITH (FORMAT csv, HEADER true)

-- Check: how many rows each table got (should be 3100, 2814, 4349, 57)
SELECT COUNT(*) AS bank_rows FROM bank_monthly;
SELECT COUNT(*) AS bank_value_rows FROM bank_value_monthly;
SELECT COUNT(*) AS app_rows FROM app_monthly;
SELECT COUNT(*) AS p2p_rows FROM p2p_p2m_monthly;
