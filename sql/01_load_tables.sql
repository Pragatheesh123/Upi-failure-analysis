-- Makes 4 tables in PostgreSQL and fills them from the clean CSV files.
-- Run from the project folder:
-- & "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d upi_failure -f sql/01_load_tables.sql
-- Then run 02_extra_columns.sql, then any question file (03 to 09).

DROP TABLE IF EXISTS bank_monthly CASCADE;
CREATE TABLE bank_monthly (
    month TEXT,
    bank_raw TEXT,
    bank TEXT,
    bank_type TEXT,
    rank_in_source INT,
    total_volume_mn NUMERIC,
    approved_pct NUMERIC,
    bd_pct NUMERIC,
    td_pct NUMERIC,
    debit_reversal_count_mn NUMERIC,
    debit_reversal_success_pct NUMERIC,
    udir_auto_update_sr_pct NUMERIC,
    udir_refund_sr_pct NUMERIC,
    source TEXT,
    is_name_corrected BOOLEAN,
    PRIMARY KEY (month, bank)
);
\copy bank_monthly FROM 'data/clean/upi_bank_monthly.csv' CSV HEADER

DROP TABLE IF EXISTS bank_value_monthly;
CREATE TABLE bank_value_monthly (
    month TEXT,
    bank_raw TEXT,
    bank TEXT,
    approved_volume_mn NUMERIC,
    value_cr NUMERIC
);
\copy bank_value_monthly FROM 'data/clean/upi_bank_value_monthly.csv' CSV HEADER

-- no primary key here: NPCI lists a few apps twice in some months
DROP TABLE IF EXISTS app_monthly;
CREATE TABLE app_monthly (
    month TEXT,
    app TEXT,
    volume_mn NUMERIC,
    value_cr NUMERIC,
    app_share_pct NUMERIC
);
\copy app_monthly FROM 'data/clean/upi_app_monthly.csv' CSV HEADER

DROP TABLE IF EXISTS p2p_p2m_monthly;
CREATE TABLE p2p_p2m_monthly (
    month TEXT PRIMARY KEY,
    p2p_volume_mn NUMERIC,
    p2p_value_cr NUMERIC,
    p2m_volume_mn NUMERIC,
    p2m_value_cr NUMERIC,
    total_volume_mn NUMERIC,
    p2m_share_pct NUMERIC
);
\copy p2p_p2m_monthly FROM 'data/clean/upi_p2p_p2m_monthly.csv' CSV HEADER

-- row counts (should be 3100, 2814, 4349, 57)
SELECT COUNT(*) FROM bank_monthly;
SELECT COUNT(*) FROM bank_value_monthly;
SELECT COUNT(*) FROM app_monthly;
SELECT COUNT(*) FROM p2p_p2m_monthly;
