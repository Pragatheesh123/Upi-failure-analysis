"""Turn the raw NPCI files into the three clean tables in data/clean/.

    python src/clean_data.py

Steps: load -> clean -> check -> save. Nothing is estimated or filled in:
a value that can't be read stays blank, and any check that fails stops the script.
Column meanings are in docs/data_dictionary.md; every choice is in docs/decisions.md.
"""
from __future__ import annotations

import glob
import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_API = ROOT / "data" / "raw" / "npci_api"
RAW_2021 = ROOT / "data" / "raw" / "npci_archive_2021_remitter_provisional.csv"
BANK_LOOKUP = ROOT / "data" / "reference" / "bank_lookup.csv"
NAME_CORRECTIONS = ROOT / "data" / "reference" / "name_corrections.csv"
CLEAN = ROOT / "data" / "clean"

FIRST_MONTH = "2021-08"        # top 50 from here on; Mar-Jul 2021 (top 30) is reference only
FESTIVAL_MONTHS = ("10", "11")  # October, November
NPCI_TD_TARGET = 1.0            # TD below 1% (NPCI circular OC 149A, June 2022)
PCT_TOLERANCE = 0.05            # Approved + BD + TD may differ from 100 by rounding only
VOLUME_MATCH_TOLERANCE = 0.02   # vol & val table must agree with the bank table within 2%


# ---------- load ----------

def load_api_table(folder: str) -> pd.DataFrame:
    """All pages of one raw table, one row per result, with the month from the file name."""
    rows = []
    for path in sorted(glob.glob(str(RAW_API / folder / "*.json"))):
        month = re.search(r"(\d{4}-\d{2})_p\d+\.json$", path).group(1)
        for record in json.loads(Path(path).read_text(encoding="utf-8"))["data"]["results"]:
            record["file_month"] = month
            rows.append(record)
    return pd.DataFrame(rows)


def to_number(values: pd.Series) -> pd.Series:
    # NPCI writes numbers as text: "7,47,792.52", "90.34%", "-" for none
    text = values.astype(str).str.replace(",", "").str.replace("%", "").str.strip()
    return pd.to_numeric(text, errors="coerce")


def name_key(name: pd.Series) -> pd.Series:
    """Spelling-proof key: 'HDFC BANK LTD.' and 'Hdfc Bank Ltd' both become 'hdfc bank'."""
    key = name.str.lower().str.replace("&", "and")
    key = key.str.replace(r"[^a-z ]", " ", regex=True)
    key = key.str.replace(r"\b(the|limited|ltd)\b", " ", regex=True)
    return key.str.replace(r"\s+", " ", regex=True).str.strip()


# ---------- clean: banks ----------

def bank_rows_from_api() -> pd.DataFrame:
    raw = load_api_table("remitter")
    return pd.DataFrame({
        "month": raw.file_month,
        "bank_raw": raw.upi_remitter_banks.str.strip(),
        "rank_in_source": to_number(raw.sr_no).astype("Int64"),
        "total_volume_mn": to_number(raw.total_volume_in_mn),
        "approved_pct": to_number(raw.approved_percent),
        "bd_pct": to_number(raw.bd_percent),
        "td_pct": to_number(raw.td_percent),
        "debit_reversal_count_mn": to_number(raw.total_debit_reversal_count_in_mn),
        "debit_reversal_success_pct": to_number(raw.debit_reversal_success_percent),
        "udir_auto_update_sr_pct": to_number(raw.udir_auto_update_sr_percent),
        "udir_refund_sr_pct": to_number(raw.udir_refund_sr_percent),
        "source": "npci_api",
    })


def bank_rows_from_2021() -> pd.DataFrame:
    raw = pd.read_csv(RAW_2021)
    raw = raw[raw.month >= FIRST_MONTH].copy()
    raw["bank_raw"] = raw.bank_raw.str.strip()
    raw["rank_in_source"] = raw.rank_in_source.astype("Int64")
    raw["source"] = "npci_archive_2021_provisional"
    return raw


def apply_name_corrections(banks: pd.DataFrame) -> pd.DataFrame:
    # NPCI printed the wrong bank name on a few rows; each fix and its evidence is in the CSV
    fixes = pd.read_csv(NAME_CORRECTIONS)
    banks["is_name_corrected"] = False
    for fix in fixes.itertuples():
        row = (banks.month == fix.month) & (banks.rank_in_source == fix.rank_in_source)
        if banks.loc[row, "bank_raw"].tolist() != [fix.bank_raw_published]:
            raise SystemExit(f"Correction no longer matches the raw data: {fix.month} rank {fix.rank_in_source}")
        banks.loc[row, "bank_raw"] = fix.bank_raw_corrected
        banks.loc[row, "is_name_corrected"] = True
    return banks


def add_bank_names_and_types(banks: pd.DataFrame) -> pd.DataFrame:
    lookup = pd.read_csv(BANK_LOOKUP)
    banks = banks.merge(lookup, on="bank_raw", how="left")
    unknown = banks[banks.bank.isna()].bank_raw.unique()
    if len(unknown):
        raise SystemExit(f"Add these names to {BANK_LOOKUP.name}: {list(unknown)}")
    return banks


def average_payment_values(lookup: pd.DataFrame) -> pd.DataFrame:
    """Rupees per successful payment, per bank per month, from NPCI's 'Top 50 Member Vol & Val'.

    That table counts approved payments only, so it is matched against
    total_volume_mn x approved_pct before being used.
    """
    raw = load_api_table("member_vol_val")
    raw = raw[raw.is_total.astype(str).str.lower() != "true"]
    key_to_bank = dict(zip(name_key(lookup.bank_raw), lookup.bank))
    values = pd.DataFrame({
        "month": raw.file_month,
        "bank": name_key(raw.bank_name.str.strip()).map(key_to_bank),
        "vv_volume_mn": to_number(raw.volume_mn),
        "vv_value_cr": to_number(raw.value_cr),
    }).dropna(subset=["bank"])
    # ₹ crore / million payments -> ₹ per payment: 1 crore = 10 million
    values["avg_payment_value_inr"] = values.vv_value_cr * 10 / values.vv_volume_mn
    return values


def add_payment_values(banks: pd.DataFrame) -> pd.DataFrame:
    values = average_payment_values(pd.read_csv(BANK_LOOKUP))
    banks = banks.merge(values, on=["month", "bank"], how="left")
    gap = (banks.vv_volume_mn / banks.approved_mn - 1).abs()
    # Keep a value only when both NPCI tables agree on the bank's volume;
    # some months in the vol & val table have banks swapped or listed twice
    banks["avg_payment_value_inr"] = banks.avg_payment_value_inr.where(gap <= VOLUME_MATCH_TOLERANCE)
    banks = (banks.sort_values("avg_payment_value_inr")
             .drop_duplicates(["month", "bank", "rank_in_source"]))
    return banks.drop(columns=["vv_volume_mn", "vv_value_cr"])


def clean_banks() -> pd.DataFrame:
    banks = pd.concat([bank_rows_from_2021(), bank_rows_from_api()], ignore_index=True)
    banks = apply_name_corrections(banks)
    banks = add_bank_names_and_types(banks)

    banks["approved_mn"] = banks.total_volume_mn * banks.approved_pct / 100
    banks["bd_failed_mn"] = banks.total_volume_mn * banks.bd_pct / 100
    banks["td_failed_mn"] = banks.total_volume_mn * banks.td_pct / 100
    banks["is_festival_month"] = banks.month.str[5:].isin(FESTIVAL_MONTHS)
    banks["above_npci_target"] = banks.td_pct > NPCI_TD_TARGET

    banks = add_payment_values(banks)
    # ₹ crore = million payments x ₹ per payment / 10
    banks["td_failed_value_cr"] = banks.td_failed_mn * banks.avg_payment_value_inr / 10

    columns = ["month", "bank_raw", "bank", "bank_type", "rank_in_source", "total_volume_mn",
               "approved_pct", "bd_pct", "td_pct", "debit_reversal_count_mn",
               "debit_reversal_success_pct", "approved_mn", "bd_failed_mn", "td_failed_mn",
               "is_festival_month", "above_npci_target", "avg_payment_value_inr",
               "td_failed_value_cr", "udir_auto_update_sr_pct", "udir_refund_sr_pct",
               "source", "is_name_corrected"]
    return banks[columns].sort_values(["month", "rank_in_source"]).reset_index(drop=True)


# ---------- clean: apps and P2P/P2M ----------

def clean_apps() -> pd.DataFrame:
    raw = load_api_table("apps")
    # Footnote marks like "Phone Pe #" are not part of the name
    app_raw = raw.application_name.fillna(raw.upi_application_name).str.replace("#", "").str.strip()
    apps = pd.DataFrame({
        "month": raw.file_month,
        "app_key": name_key(app_raw).str.replace(" ", ""),
        "app_raw": app_raw,
        "volume_mn": to_number(raw.total_volume_mn),
        "value_cr": to_number(raw.total_value_cr),
    })
    # One name per app: the spelling NPCI used most recently
    latest_name = apps.sort_values("month").groupby("app_key").app_raw.last()
    apps["app"] = apps.app_key.map(latest_name)
    month_total = apps.groupby("month").volume_mn.transform("sum")
    apps["app_share_pct"] = apps.volume_mn / month_total * 100
    columns = ["month", "app", "volume_mn", "value_cr", "app_share_pct"]
    return apps[columns].sort_values(["month", "volume_mn"], ascending=[True, False]).reset_index(drop=True)


def clean_p2p_p2m() -> pd.DataFrame:
    raw = load_api_table("p2p_p2m")
    p2p = pd.DataFrame({
        "month": raw.file_month,
        "p2p_volume_mn": to_number(raw.p_2_p_volume_mn),
        "p2p_value_cr": to_number(raw.p_2_p_value_cr),
        "p2m_volume_mn": to_number(raw.p_2_m_volume_mn),
        "p2m_value_cr": to_number(raw.p_2_m_value_cr),
        "total_volume_mn": to_number(raw.total_volume_mn),
    })
    p2p["p2m_share_pct"] = p2p.p2m_volume_mn / (p2p.p2p_volume_mn + p2p.p2m_volume_mn) * 100
    return p2p.sort_values("month").reset_index(drop=True)


# ---------- check ----------

def check_banks(banks: pd.DataFrame) -> None:
    pct_sum = banks.approved_pct + banks.bd_pct + banks.td_pct
    bad_sum = banks[(pct_sum - 100).abs() > PCT_TOLERANCE]
    if len(bad_sum):
        raise SystemExit(f"Approved + BD + TD is not 100 on {len(bad_sum)} rows:\n{bad_sum.head()}")

    duplicates = banks[banks.duplicated(["month", "bank"], keep=False)]
    if len(duplicates):
        raise SystemExit(f"Duplicate bank-months:\n{duplicates[['month', 'bank_raw', 'bank']]}")

    all_months = pd.period_range(FIRST_MONTH, banks.month.max(), freq="M").astype(str)
    missing = sorted(set(all_months) - set(banks.month))
    if missing:
        raise SystemExit(f"Missing months: {missing}")

    banks_per_month = banks.groupby("month").size()
    if (banks_per_month != 50).any():
        raise SystemExit(f"Months without 50 banks:\n{banks_per_month[banks_per_month != 50]}")


def check_p2p_p2m(p2p: pd.DataFrame) -> None:
    # P2P + P2M should make up the month's total
    gap = (p2p.p2p_volume_mn + p2p.p2m_volume_mn - p2p.total_volume_mn).abs()
    if (gap > 1).any():
        raise SystemExit(f"P2P + P2M differs from total by more than 1 Mn:\n{p2p[gap > 1]}")


# ---------- save ----------

def main() -> int:
    banks = clean_banks()
    apps = clean_apps()
    p2p = clean_p2p_p2m()

    check_banks(banks)
    check_p2p_p2m(p2p)

    CLEAN.mkdir(parents=True, exist_ok=True)
    banks.to_csv(CLEAN / "upi_bank_monthly.csv", index=False)
    apps.to_csv(CLEAN / "upi_app_monthly.csv", index=False)
    p2p.to_csv(CLEAN / "upi_p2p_p2m_monthly.csv", index=False)

    with_value = banks.avg_payment_value_inr.notna()
    print(f"upi_bank_monthly.csv    {len(banks):>5} rows, {banks.month.min()} to {banks.month.max()}, "
          f"{banks.bank.nunique()} banks")
    print(f"  payment value found for {with_value.sum()} of {(banks.source == 'npci_api').sum()} "
          f"bank-months from the feed")
    print(f"upi_app_monthly.csv     {len(apps):>5} rows, {apps.app.nunique()} apps")
    print(f"upi_p2p_p2m_monthly.csv {len(p2p):>5} rows")
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
