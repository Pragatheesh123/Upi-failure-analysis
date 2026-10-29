# STEP 2: CLEAN THE DATA
#
# Reads the raw NPCI files from data/raw/ and makes clean tables in data/clean/:
#   upi_bank_monthly.csv      one row per bank per month
#   upi_app_monthly.csv       one row per app per month
#   upi_p2p_p2m_monthly.csv   one row per month
#   upi_clean_data.xlsx       all of the above + a sheet listing every change made
#
# Run from the project folder:  python src/step2_clean_data.py
# Nothing is guessed or filled in. If a check fails, the script stops.

import glob
import json
import os

import pandas as pd

changes = []  # every cleaning step adds a line here; it becomes the "Changes made" sheet in Excel


def log_change(step, what, why, rows, example):
    changes.append({"Step": step, "What we did": what, "Why": why,
                    "Rows affected": rows, "Example": example})
    print(f"Step {step}: {what} ({rows} rows)")


def read_raw_table(folder):
    # Each raw file is one page (10 rows) of one month. Put all pages of a table together.
    rows = []
    for file in sorted(glob.glob(f"data/raw/npci_api/{folder}/*.json")):
        month = os.path.basename(file)[:7]  # file name starts with the month, e.g. 2026-09_p1.json
        with open(file, encoding="utf-8") as f:
            page = json.load(f)
        for row in page["data"]["results"]:
            row["file_month"] = month
            rows.append(row)
    return pd.DataFrame(rows)


def to_number(column):
    # NPCI writes numbers as text, like "7,47,792.52" or "90.34%". Remove , and % then convert.
    # Anything that still isn't a number (like "-") becomes blank, never a guess.
    text = column.astype(str).str.replace(",", "").str.replace("%", "").str.strip()
    return pd.to_numeric(text, errors="coerce")


# =====================================================================
# BANK TABLE
# =====================================================================

# Step 1: read the raw bank table (Jan 2022 to Sep 2026) and pick the columns we need
raw = read_raw_table("remitter")
banks = pd.DataFrame()
banks["month"] = raw["file_month"]
banks["bank_raw"] = raw["upi_remitter_banks"].str.strip()   # some names had extra spaces or line breaks
banks["rank_in_source"] = to_number(raw["sr_no"])
banks["total_volume_mn"] = to_number(raw["total_volume_in_mn"])
banks["approved_pct"] = to_number(raw["approved_percent"])
banks["bd_pct"] = to_number(raw["bd_percent"])
banks["td_pct"] = to_number(raw["td_percent"])
banks["debit_reversal_count_mn"] = to_number(raw["total_debit_reversal_count_in_mn"])
banks["debit_reversal_success_pct"] = to_number(raw["debit_reversal_success_percent"])
banks["udir_auto_update_sr_pct"] = to_number(raw["udir_auto_update_sr_percent"])
banks["udir_refund_sr_pct"] = to_number(raw["udir_refund_sr_percent"])
banks["source"] = "npci_api"
log_change(1, "Joined all raw pages of the bank table into one table and turned text into numbers",
           "NPCI sends 10 rows per file and writes numbers as text", len(banks),
           f'"{raw["approved_percent"][0]}" -> {banks["approved_pct"][0]}')

# Step 2: add Aug-Dec 2021 from the earlier archive copy (marked provisional)
old = pd.read_csv("data/raw/npci_archive_2021_remitter_provisional.csv")
old = old[old["month"] >= "2021-08"]   # top 50 banks start in Aug 2021; Mar-Jul 2021 was top 30
old["bank_raw"] = old["bank_raw"].str.strip()
old["source"] = "npci_archive_2021_provisional"
banks = pd.concat([old, banks], ignore_index=True)
log_change(2, "Added Aug-Dec 2021 from the NPCI archive copy, marked provisional",
           "The data feed starts in Jan 2022; 2021 adds one more festival season", len(old),
           "source = npci_archive_2021_provisional")

# Step 3: fix 2 rows where NPCI printed the wrong bank name
# In both months "Slice" is listed twice and one bank is missing. The extra row's
# volume, approval % and rank match the missing bank in the months before and after.
# Only the name changes, no numbers. Evidence: docs/decisions.md (29 Oct 2026).
banks["is_name_corrected"] = False
name_fixes = [
    ("2026-03", 36, "Slice Small Finance Bank Limited", "Tamilnad Mercantile Bank Limited"),
    ("2026-06", 38, "Slice Small Finance Bank Limited", "Ujjivan Small Finance Bank Limited"),
]
for month, rank, wrong_name, right_name in name_fixes:
    row = (banks["month"] == month) & (banks["rank_in_source"] == rank) & (banks["bank_raw"] == wrong_name)
    if row.sum() != 1:
        raise SystemExit(f"Name fix for {month} rank {rank} no longer matches the raw data")
    banks.loc[row, "bank_raw"] = right_name
    banks.loc[row, "is_name_corrected"] = True
log_change(3, "Fixed 2 rows where NPCI printed the wrong bank name",
           "Slice was listed twice while TMB (Mar 2026) and Ujjivan (Jun 2026) were missing", 2,
           "Mar 2026 rank 36: Slice -> Tamilnad Mercantile Bank")

# Step 4: one standard name and a bank type for every spelling, from data/bank_names.csv
bank_names = pd.read_csv("data/bank_names.csv")
banks = banks.merge(bank_names, on="bank_raw", how="left")
unknown = banks[banks["bank"].isna()]["bank_raw"].unique()
if len(unknown) > 0:
    raise SystemExit(f"New spelling(s), add them to data/bank_names.csv: {list(unknown)}")
renamed = (banks["bank_raw"] != banks["bank"]).sum()
log_change(4, f"Gave every bank one standard name and a bank type "
              f"({banks['bank_raw'].nunique()} spellings -> {banks['bank'].nunique()} banks)",
           "NPCI spells the same bank differently across months", renamed,
           '"HDFC BANK LTD." and "Hdfc Bank Ltd" -> "HDFC Bank", type Private')

# Step 5: calculated columns
banks["approved_mn"] = banks["total_volume_mn"] * banks["approved_pct"] / 100
banks["bd_failed_mn"] = banks["total_volume_mn"] * banks["bd_pct"] / 100
banks["td_failed_mn"] = banks["total_volume_mn"] * banks["td_pct"] / 100
banks["is_festival_month"] = banks["month"].str[5:].isin(["10", "11"])   # October or November
banks["above_npci_target"] = banks["td_pct"] > 1.0   # NPCI target: TD below 1% (circular OC 149A)
log_change(5, "Added calculated columns: approved_mn, bd_failed_mn, td_failed_mn, "
              "is_festival_month, above_npci_target",
           "Payments count (not just %) is needed to add banks up and to cost failures", len(banks),
           "td_failed_mn = total_volume_mn x td_pct / 100")

# Step 6: average payment value per bank (in rupees), from NPCI's "Top 50 Member Vol & Val" table.
# That table counts approved payments only, so we use a bank's value only when its volume
# matches our approved_mn within 2%. Some months in it have banks swapped (e.g. Axis and Yes, early 2023).
raw_values = read_raw_table("member_vol_val")
values = pd.DataFrame()
values["month"] = raw_values["file_month"]
values["bank_raw"] = raw_values["bank_name"].str.strip()
values["vv_volume_mn"] = to_number(raw_values["volume_mn"])
values["vv_value_cr"] = to_number(raw_values["value_cr"])
values = values.merge(bank_names[["bank_raw", "bank"]], on="bank_raw")   # also drops "Total" and "Others"
values["avg_payment_value_inr"] = values["vv_value_cr"] * 10 / values["vv_volume_mn"]   # 1 crore = 10 million
values = values[["month", "bank", "vv_volume_mn", "avg_payment_value_inr"]]

banks = banks.merge(values, on=["month", "bank"], how="left")
volumes_match = (banks["vv_volume_mn"] / banks["approved_mn"] - 1).abs() <= 0.02
banks.loc[~volumes_match, "avg_payment_value_inr"] = None
# A bank listed twice in that table gives two rows here: keep the one whose volume matched
banks = banks.sort_values("avg_payment_value_inr").drop_duplicates(["month", "bank", "rank_in_source"])
banks["td_failed_value_cr"] = banks["td_failed_mn"] * banks["avg_payment_value_inr"] / 10   # Rs crore
log_change(6, "Added average payment value (Rs) and the Rs crore value of system-failed payments",
           "Needed for question 4 (cost of failures); used only where both NPCI tables agree",
           int(banks["avg_payment_value_inr"].notna().sum()),
           "avg_payment_value_inr = value_cr x 10 / volume_mn")

# Put the columns in a fixed order and sort by month and rank
banks["rank_in_source"] = banks["rank_in_source"].astype(int)
banks = banks[["month", "bank_raw", "bank", "bank_type", "rank_in_source", "total_volume_mn",
               "approved_pct", "bd_pct", "td_pct", "debit_reversal_count_mn",
               "debit_reversal_success_pct", "approved_mn", "bd_failed_mn", "td_failed_mn",
               "is_festival_month", "above_npci_target", "avg_payment_value_inr",
               "td_failed_value_cr", "udir_auto_update_sr_pct", "udir_refund_sr_pct",
               "source", "is_name_corrected"]]
banks = banks.sort_values(["month", "rank_in_source"]).reset_index(drop=True)

# =====================================================================
# APPS TABLE
# =====================================================================

# Step 7: apps - one row per app per month, with its share of all app payments
raw_apps = read_raw_table("apps")
apps = pd.DataFrame()
apps["month"] = raw_apps["file_month"]
# NPCI renamed the column in later months, so take whichever one has the name
apps["app_raw"] = raw_apps["application_name"].fillna(raw_apps["upi_application_name"])
apps["app_raw"] = apps["app_raw"].str.replace("#", "").str.strip()   # "#" is a footnote mark, not part of the name
apps["volume_mn"] = to_number(raw_apps["total_volume_mn"])
apps["value_cr"] = to_number(raw_apps["total_value_cr"])
# Same app, different spelling ("PhonePe" / "Phone Pe", "... Digital" / "... Digital Limited"):
# compare names without case, spaces, dots or "limited", then use the spelling NPCI used most recently
apps["app_key"] = apps["app_raw"].str.lower().str.replace("limited", "").str.replace(r"[^a-z]", "", regex=True)
latest_spelling = apps.sort_values("month").groupby("app_key")["app_raw"].last()
apps["app"] = apps["app_key"].map(latest_spelling)
apps["app_share_pct"] = apps["volume_mn"] / apps.groupby("month")["volume_mn"].transform("sum") * 100
apps = apps.sort_values(["month", "volume_mn"], ascending=[True, False])
apps = apps[["month", "app", "volume_mn", "value_cr", "app_share_pct"]].reset_index(drop=True)
log_change(7, f"Apps: joined pages, removed footnote marks, one name per app "
              f"({raw_apps['application_name'].nunique()} spellings -> {apps['app'].nunique()} apps), added share %",
           "Supporting chart on app market share", len(apps), '"Phone Pe #" -> "Phone Pe"')

# =====================================================================
# P2P / P2M TABLE
# =====================================================================

# Step 8: person-to-person (P2P) vs person-to-merchant (P2M, shop/checkout) payments per month
raw_p2p = read_raw_table("p2p_p2m")
p2p = pd.DataFrame()
p2p["month"] = raw_p2p["file_month"]
p2p["p2p_volume_mn"] = to_number(raw_p2p["p_2_p_volume_mn"])
p2p["p2p_value_cr"] = to_number(raw_p2p["p_2_p_value_cr"])
p2p["p2m_volume_mn"] = to_number(raw_p2p["p_2_m_volume_mn"])
p2p["p2m_value_cr"] = to_number(raw_p2p["p_2_m_value_cr"])
p2p["total_volume_mn"] = to_number(raw_p2p["total_volume_mn"])
p2p["p2m_share_pct"] = p2p["p2m_volume_mn"] / (p2p["p2p_volume_mn"] + p2p["p2m_volume_mn"]) * 100
p2p = p2p.sort_values("month").reset_index(drop=True)
log_change(8, "P2P/P2M: turned text into numbers and added the merchant (P2M) share %",
           "Question 5: how many checkout payments were put at risk", len(p2p),
           f'"{raw_p2p["p_2_m_volume_mn"].iloc[-1]}" -> {p2p["p2m_volume_mn"].iloc[-1]}')

# =====================================================================
# CHECKS - the script stops if any of these fail
# =====================================================================

# Check 1: Approved + BD + TD must add up to 100% (allowing 0.05 for rounding)
total_pct = banks["approved_pct"] + banks["bd_pct"] + banks["td_pct"]
bad_rows = banks[(total_pct - 100).abs() > 0.05]
if len(bad_rows) > 0:
    raise SystemExit(f"Approved + BD + TD is not 100 on these rows:\n{bad_rows}")

# Check 2: each bank only once per month
duplicates = banks[banks.duplicated(["month", "bank"], keep=False)]
if len(duplicates) > 0:
    raise SystemExit(f"Bank listed twice in a month:\n{duplicates[['month', 'bank_raw', 'bank']]}")

# Check 3: no month missing, and exactly 50 banks in every month
all_months = pd.period_range("2021-08", banks["month"].max(), freq="M").astype(str)
missing_months = sorted(set(all_months) - set(banks["month"]))
if missing_months:
    raise SystemExit(f"Missing months: {missing_months}")
banks_per_month = banks.groupby("month").size()
if (banks_per_month != 50).any():
    raise SystemExit(f"Months without 50 banks:\n{banks_per_month[banks_per_month != 50]}")

# Check 4: P2P + P2M must equal NPCI's monthly total (within 1 million)
gap = (p2p["p2p_volume_mn"] + p2p["p2m_volume_mn"] - p2p["total_volume_mn"]).abs()
if (gap > 1).any():
    raise SystemExit(f"P2P + P2M is not equal to the total:\n{p2p[gap > 1]}")

print("All checks passed: rows add to 100%, no duplicates, no missing months, 50 banks every month.")

# =====================================================================
# SAVE
# =====================================================================

os.makedirs("data/clean", exist_ok=True)
banks.to_csv("data/clean/upi_bank_monthly.csv", index=False)
apps.to_csv("data/clean/upi_app_monthly.csv", index=False)
p2p.to_csv("data/clean/upi_p2p_p2m_monthly.csv", index=False)

# Excel copy to look at: the changes first, then the bank-name list, then the clean tables
names_used = banks.groupby(["bank_raw", "bank", "bank_type"]).size().reset_index(name="rows")
with pd.ExcelWriter("data/clean/upi_clean_data.xlsx") as excel:
    pd.DataFrame(changes).to_excel(excel, sheet_name="Changes made", index=False)
    names_used.to_excel(excel, sheet_name="Bank names", index=False)
    banks.to_excel(excel, sheet_name="Banks", index=False)
    apps.to_excel(excel, sheet_name="Apps", index=False)
    p2p.to_excel(excel, sheet_name="P2P P2M", index=False)
    for sheet in excel.sheets.values():   # widen columns so the text is readable
        sheet.freeze_panes = "A2"
        for column in sheet.columns:
            longest = max(len(str(cell.value or "")) for cell in column[:200])
            sheet.column_dimensions[column[0].column_letter].width = min(longest + 2, 60)

print(f"Saved: banks {len(banks)} rows, apps {len(apps)} rows, P2P/P2M {len(p2p)} rows")
print("Open data/clean/upi_clean_data.xlsx to see the clean tables and every change made.")
