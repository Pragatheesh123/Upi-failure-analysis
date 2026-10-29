import sys

import pandas as pd

sys.path.insert(0, "src")
from clean_data import name_key, to_number  # noqa: E402


def test_to_number_reads_npci_text():
    values = to_number(pd.Series(["7,47,792.52", "90.34%", " 0.03% ", "-", "6734.080234"]))
    assert values.tolist()[:3] == [747792.52, 90.34, 0.03]
    assert pd.isna(values[3])
    assert values[4] == 6734.080234


def test_name_key_ignores_case_punctuation_and_ltd():
    spellings = pd.Series(["HDFC BANK LTD.", "Hdfc Bank Ltd", "HDFC Bank Limited"])
    assert name_key(spellings).unique().tolist() == ["hdfc bank"]
    assert name_key(pd.Series(["Punjab & Sind Bank"]))[0] == "punjab and sind bank"


def test_clean_bank_table_matches_source():
    banks = pd.read_csv("data/clean/upi_bank_monthly.csv")
    sbi = banks[(banks["month"] == "2026-09") & (banks["bank"] == "State Bank of India")].iloc[0]
    # Values as published by NPCI for Sep 2026
    assert (sbi["approved_pct"], sbi["bd_pct"], sbi["td_pct"]) == (90.34, 9.28, 0.38)
    assert sbi["bank_type"] == "Public"
    assert not banks.duplicated(["month", "bank"]).any()
