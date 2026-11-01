# STEP 2: CLEAN THE DATA
# Takes the raw NPCI files in data/raw/ and saves clean files in data/clean/ and excel/.
# Only cleaning here. Calculations (failed payments, Rs value) are done in SQL: sql/02_extra_columns.sql
# Run: python python/step2_clean_data.py
# If anything looks wrong, the script stops with a message.

import pandas as pd
from openpyxl.styles import PatternFill


# ---------- 1. Read the bank file ----------
raw = pd.read_csv("data/raw/npci_remitter.csv", dtype=str)   # dtype=str: read everything as text first

# Drop NPCI's "month" column (it only says "Jan"). We use file_month instead ("2022-01").
# Give the columns short, clear names.
banks = raw.drop(columns="month").rename(columns={
    "file_month": "month",
    "upi_remitter_banks": "bank_raw",
    "sr_no": "rank_in_source",
    "total_volume_in_mn": "total_volume_mn",
    "approved_percent": "approved_pct",
    "bd_percent": "bd_pct",
    "td_percent": "td_pct",
    "total_debit_reversal_count_in_mn": "debit_reversal_count_mn",
    "debit_reversal_success_percent": "debit_reversal_success_pct",
    "udir_auto_update_sr_percent": "udir_auto_update_sr_pct",
    "udir_refund_sr_percent": "udir_refund_sr_pct",
})
number_columns = ["rank_in_source", "total_volume_mn", "approved_pct", "bd_pct", "td_pct",
                  "debit_reversal_count_mn", "debit_reversal_success_pct",
                  "udir_auto_update_sr_pct", "udir_refund_sr_pct"]
banks = banks[["month", "bank_raw"] + number_columns]   # keep only the columns we need
banks["bank_raw"] = banks["bank_raw"].str.strip()       # remove extra spaces around names
banks["source"] = "npci_api"
banks["npci_row"] = range(len(banks))                   # row number, used later for the Excel comparison

# Turn text into numbers: "90.34%" -> 90.34 and "7,47,792.52" -> 747792.52
# errors="coerce" means: if it's not a number (like "-"), leave it blank
for column in number_columns:
    banks[column] = pd.to_numeric(banks[column].str.replace(",", "").str.replace("%", ""), errors="coerce")
print("1. Read", len(banks), "bank rows")


# ---------- 2. Add Aug-Dec 2021 ----------
# The NPCI feed starts in Jan 2022, so these 5 months come from the NPCI archive page.
old = pd.read_csv("data/raw/npci_archive_2021_remitter_provisional.csv")
old = old[old["month"] >= "2021-08"]   # from Aug 2021 NPCI lists the top 50 banks (before that, top 30)
old["bank_raw"] = old["bank_raw"].str.strip()
old["source"] = "npci_archive_2021_provisional"
banks = pd.concat([old, banks], ignore_index=True)   # put the two tables one under the other
print("2. Added", len(old), "rows for Aug-Dec 2021")


# ---------- 3. Fix 2 wrong bank names ----------
# In Mar and Jun 2026 NPCI wrote "Slice" twice, and one bank went missing.
# The second "Slice" row has the missing bank's numbers, so we put the right name back.
name_fixes = [
    ("2026-03", 36, "Tamilnad Mercantile Bank Limited"),
    ("2026-06", 38, "Ujjivan Small Finance Bank Limited"),
]
banks["is_name_corrected"] = False
for month, rank, right_name in name_fixes:
    row = (banks["month"] == month) & (banks["rank_in_source"] == rank)
    if banks.loc[row, "bank_raw"].tolist() != ["Slice Small Finance Bank Limited"]:
        raise SystemExit(f"Name fix for {month} rank {rank} does not match the raw data any more")
    banks.loc[row, "bank_raw"] = right_name
    banks.loc[row, "is_name_corrected"] = True
print("3. Fixed 2 wrong bank names")

# NPCI left out the decimal point in Aug 2022 refund success % ("9123.00%" should be 91.23%)
aug_2022 = banks["month"] == "2022-08"
banks.loc[aug_2022, "debit_reversal_success_pct"] = banks.loc[aug_2022, "debit_reversal_success_pct"] / 100
print("3. Fixed Aug 2022 refund success % (divided by 100)")


# ---------- 4. One name per bank ----------
# NPCI spells banks differently ("HDFC BANK LTD", "Hdfc Bank Ltd").
# data/bank_names.csv lists every spelling with its standard name and bank type. It works like VLOOKUP.
bank_names = pd.read_csv("data/bank_names.csv")
banks = banks.merge(bank_names, on="bank_raw", how="left")

unknown_names = banks[banks["bank"].isna()]["bank_raw"].unique()
if len(unknown_names) > 0:
    raise SystemExit(f"Add these new spellings to data/bank_names.csv: {list(unknown_names)}")
print("4.", banks["bank_raw"].nunique(), "spellings ->", banks["bank"].nunique(), "banks")

# On 1 May 2025 some Gramin (rural) banks merged into one bank per state ("One State, One RRB").
# NPCI keeps switching between the old and the new names after that, so from May 2025 we give
# the old names the new bank's name. Before May 2025 they stay separate, as they really were.
merged_banks = {
    "Baroda U.P. Bank": "Uttar Pradesh Gramin Bank",
    "Andhra Pragathi Grameena Bank": "Andhra Pradesh Grameena Bank",
    "Chaitanya Godavari Grameena Bank": "Andhra Pradesh Grameena Bank",
    "Andhra Pradesh Grameena Vikas Bank": "Andhra Pradesh Grameena Bank",
    "Rajasthan Marudhara Gramin Bank": "Rajasthan Gramin Bank",
}
after_merger = banks["month"] >= "2025-05"
banks.loc[after_merger, "bank"] = banks.loc[after_merger, "bank"].replace(merged_banks)
print("4. Merged Gramin banks counted once from May 2025:", after_merger.sum(), "rows checked")


# ---------- 5. Bank payment values ----------
# A second NPCI table: each bank's approved payments (in millions) and their value (in Rs crore).
# SQL uses it later to work out the average payment in Rs.
raw_values = pd.read_csv("data/raw/npci_member_vol_val.csv", dtype=str)
values = raw_values.drop(columns="month").rename(columns={"file_month": "month", "bank_name": "bank_raw",
                                                          "volume_mn": "approved_volume_mn"})
values = values[["month", "bank_raw", "approved_volume_mn", "value_cr"]]
values["bank_raw"] = values["bank_raw"].str.strip()
for column in ["approved_volume_mn", "value_cr"]:
    values[column] = pd.to_numeric(values[column].str.replace(",", ""), errors="coerce")
values = values.merge(bank_names[["bank_raw", "bank"]], on="bank_raw")   # standard names (also drops "Total" rows)
values_after_merger = values["month"] >= "2025-05"                       # same merger rule as the bank table
values.loc[values_after_merger, "bank"] = values.loc[values_after_merger, "bank"].replace(merged_banks)
values = values[["month", "bank_raw", "bank", "approved_volume_mn", "value_cr"]].sort_values(["month", "bank"])
print("5.", len(values), "bank value rows")


# ---------- 6. Before vs after (for Excel) ----------
# NPCI's original value and our clean value side by side. Red = we changed it.
after = banks[banks["source"] == "npci_api"].sort_values("npci_row").reset_index(drop=True)   # same order as raw
compare = pd.DataFrame()
compare["Month"] = after["month"]
compare["Rank"] = after["rank_in_source"].astype(int)
compare["Bank (NPCI)"] = raw["upi_remitter_banks"]
compare["Bank (clean)"] = after["bank"]
compare["Approved % (NPCI)"] = raw["approved_percent"]
compare["Approved % (clean)"] = after["approved_pct"]
compare["BD % (NPCI)"] = raw["bd_percent"]
compare["BD % (clean)"] = after["bd_pct"]
compare["TD % (NPCI)"] = raw["td_percent"]
compare["TD % (clean)"] = after["td_pct"]
compare["Debit reversals (NPCI)"] = raw["total_debit_reversal_count_in_mn"]
compare["Debit reversals (clean)"] = after["debit_reversal_count_mn"]
compare["Refund success % (NPCI)"] = raw["debit_reversal_success_percent"]
compare["Refund success % (clean)"] = after["debit_reversal_success_pct"]

# Which cells to colour red: a changed bank name, or a value that became blank ("-" or "NaN%")
red_cells = pd.DataFrame()
red_cells["Bank (clean)"] = compare["Bank (NPCI)"] != compare["Bank (clean)"]
red_cells["Debit reversals (clean)"] = compare["Debit reversals (NPCI)"].notna() & compare["Debit reversals (clean)"].isna()
red_cells["Refund success % (clean)"] = compare["Refund success % (NPCI)"].notna() & compare["Refund success % (clean)"].isna()
red_cells["Refund success % (clean)"] = red_cells["Refund success % (clean)"] | (compare["Month"] == "2022-08")   # decimal fix


# ---------- 7. Final bank table ----------
banks["rank_in_source"] = banks["rank_in_source"].astype(int)
banks = banks[["month", "bank_raw", "bank", "bank_type", "rank_in_source", "total_volume_mn",
               "approved_pct", "bd_pct", "td_pct", "debit_reversal_count_mn",
               "debit_reversal_success_pct", "udir_auto_update_sr_pct", "udir_refund_sr_pct",
               "source", "is_name_corrected"]]
banks = banks.sort_values(["month", "rank_in_source"]).reset_index(drop=True)


# ---------- 8. Apps ----------
raw_apps = pd.read_csv("data/raw/npci_apps.csv", dtype=str)
apps = raw_apps.drop(columns="month").rename(columns={"file_month": "month", "total_volume_mn": "volume_mn", "total_value_cr": "value_cr"})
apps["app_raw"] = apps["application_name"].fillna(apps["upi_application_name"])   # NPCI renamed this column later
apps["app_raw"] = apps["app_raw"].str.replace("#", "").str.strip()                # "#" is just a footnote mark
for column in ["volume_mn", "value_cr"]:
    apps[column] = pd.to_numeric(apps[column].str.replace(",", ""), errors="coerce")

# One name per app, from data/app_names.csv (works like VLOOKUP, same as the bank names)
app_names = pd.read_csv("data/app_names.csv")
apps = apps.merge(app_names, on="app_raw", how="left")
unknown_apps = apps[apps["app"].isna()]["app_raw"].unique()
if len(unknown_apps) > 0:
    raise SystemExit(f"Add these new app spellings to data/app_names.csv: {list(unknown_apps)}")

# Each app's share of all payments that month
apps["app_share_pct"] = apps["volume_mn"] / apps.groupby("month")["volume_mn"].transform("sum") * 100
apps = apps.sort_values(["month", "volume_mn"], ascending=[True, False])
apps = apps[["month", "app", "volume_mn", "value_cr", "app_share_pct"]].reset_index(drop=True)
print("8.", apps["app"].nunique(), "apps")


# ---------- 9. P2P and P2M ----------
# P2P = person to person, P2M = person to merchant (shop or checkout payments)
raw_p2p = pd.read_csv("data/raw/npci_p2p_p2m.csv", dtype=str)
p2p = raw_p2p.drop(columns="month").rename(columns={"file_month": "month",
                                                    "p_2_p_volume_mn": "p2p_volume_mn", "p_2_p_value_cr": "p2p_value_cr",
                                                    "p_2_m_volume_mn": "p2m_volume_mn", "p_2_m_value_cr": "p2m_value_cr"})
p2p_numbers = ["p2p_volume_mn", "p2p_value_cr", "p2m_volume_mn", "p2m_value_cr", "total_volume_mn"]
p2p = p2p[["month"] + p2p_numbers]
for column in p2p_numbers:
    p2p[column] = pd.to_numeric(p2p[column].str.replace(",", ""), errors="coerce")
p2p["p2m_share_pct"] = p2p["p2m_volume_mn"] / (p2p["p2p_volume_mn"] + p2p["p2m_volume_mn"]) * 100
p2p = p2p.sort_values("month").reset_index(drop=True)
print("9. P2P/P2M done")


# ---------- 10. Checks (the script stops if one fails) ----------
# Approved + BD + TD should be 100% (we allow 0.05 for rounding)
total_pct = banks["approved_pct"] + banks["bd_pct"] + banks["td_pct"]
if ((total_pct - 100).abs() > 0.05).any():
    raise SystemExit(f"Approved + BD + TD is not 100:\n{banks[(total_pct - 100).abs() > 0.05]}")

# Each bank only once per month
if banks.duplicated(["month", "bank"]).any():
    raise SystemExit(f"Bank listed twice in a month:\n{banks[banks.duplicated(['month', 'bank'], keep=False)]}")

# No month missing between Aug 2021 and the latest month
all_months = pd.Series(pd.period_range("2021-08", banks["month"].max(), freq="M").astype(str))
missing_months = all_months[~all_months.isin(banks["month"])]
if len(missing_months) > 0:
    raise SystemExit(f"Missing months: {list(missing_months)}")

# 50 banks every month
banks_per_month = banks.groupby("month").size()
if (banks_per_month != 50).any():
    raise SystemExit(f"Months without 50 banks:\n{banks_per_month[banks_per_month != 50]}")

# Refund success can't be more than 100%
if (banks["debit_reversal_success_pct"] > 100).any():
    raise SystemExit(f"Refund success above 100%:\n{banks[banks['debit_reversal_success_pct'] > 100]}")

# P2P + P2M should equal NPCI's total (within 1 million)
gap = (p2p["p2p_volume_mn"] + p2p["p2m_volume_mn"] - p2p["total_volume_mn"]).abs()
if (gap > 1).any():
    raise SystemExit(f"P2P + P2M is not equal to the total:\n{p2p[gap > 1]}")
print("10. All checks passed")


# ---------- 11. Save ----------
banks.to_csv("data/clean/upi_bank_monthly.csv", index=False)
values.to_csv("data/clean/upi_bank_value_monthly.csv", index=False)
apps.to_csv("data/clean/upi_app_monthly.csv", index=False)
p2p.to_csv("data/clean/upi_p2p_p2m_monthly.csv", index=False)

with pd.ExcelWriter("excel/upi_clean_data.xlsx") as excel:
    compare.to_excel(excel, sheet_name="Before vs after", index=False)
    bank_names.to_excel(excel, sheet_name="Bank names", index=False)
    app_names.to_excel(excel, sheet_name="App names", index=False)
    banks.to_excel(excel, sheet_name="Clean banks", index=False)
    values.to_excel(excel, sheet_name="Clean bank values", index=False)
    apps.to_excel(excel, sheet_name="Clean apps", index=False)
    p2p.to_excel(excel, sheet_name="Clean P2P P2M", index=False)

    # Colour the changed cells red (+2 because Excel starts at row 1 and row 1 is the header)
    red = PatternFill(fill_type="solid", start_color="FFC7CE")
    sheet = excel.sheets["Before vs after"]
    for column in red_cells.columns:
        column_number = compare.columns.get_loc(column) + 1
        for row in red_cells.index[red_cells[column]]:
            sheet.cell(row=row + 2, column=column_number).fill = red

    # Wider columns so the text fits
    for sheet in excel.sheets.values():
        for column in sheet.columns:
            sheet.column_dimensions[column[0].column_letter].width = 30
print("11. Saved data/clean/ and excel/upi_clean_data.xlsx")
