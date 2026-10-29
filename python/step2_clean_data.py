# STEP 2: CLEAN THE DATA
# Reads data/raw/, writes data/clean/ (3 CSVs) and excel/upi_clean_data.xlsx.
# Run from the project folder: python python/step2_clean_data.py
# Nothing is guessed or filled in. If a check fails, the script stops.

import pandas as pd
from openpyxl.styles import PatternFill

changes = []  # one line per step, for the "Changes made" sheet


# Step 1: read the raw bank table, keep the columns we need, clear names
raw = pd.read_csv("data/raw/npci_remitter.csv", dtype=str)
banks = raw.drop(columns="month").rename(columns={   # NPCI's "month" only says "Jan"; file_month says "2022-01"
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
banks = banks[["month", "bank_raw"] + number_columns]
banks["bank_raw"] = banks["bank_raw"].str.strip()
banks["source"] = "npci_api"
banks["npci_row"] = range(len(banks))   # to line up before vs after in Excel

# Text to numbers: "90.34%" -> 90.34, "7,47,792.52" -> 747792.52, "-" -> blank
banks[number_columns] = banks[number_columns].replace({",": "", "%": ""}, regex=True).apply(pd.to_numeric, errors="coerce")

print(f"Step 1: read {len(banks)} bank rows")
changes.append({"Step": 1, "What we did": "Turned text into numbers; '-' and 'NaN%' became blank",
                "Why": 'NPCI writes numbers as text, like "90.34%"', "Rows": len(banks)})


# Step 2: add Aug-Dec 2021 from the archive copy (top 50 banks start in Aug 2021)
old = pd.read_csv("data/raw/npci_archive_2021_remitter_provisional.csv")
old = old[old["month"] >= "2021-08"]
old["bank_raw"] = old["bank_raw"].str.strip()
old["source"] = "npci_archive_2021_provisional"
banks = pd.concat([old, banks], ignore_index=True)

print(f"Step 2: added {len(old)} rows for Aug-Dec 2021")
changes.append({"Step": 2, "What we did": "Added Aug-Dec 2021 from the NPCI archive copy, marked provisional",
                "Why": "The data feed starts in Jan 2022", "Rows": len(old)})


# Step 3: NPCI listed Slice twice in Mar and Jun 2026; the extra row's numbers match the missing bank
name_fixes = [
    ("2026-03", 36, "Tamilnad Mercantile Bank Limited"),
    ("2026-06", 38, "Ujjivan Small Finance Bank Limited"),
]
banks["is_name_corrected"] = False
for month, rank, right_name in name_fixes:
    row = (banks["month"] == month) & (banks["rank_in_source"] == rank)
    if banks.loc[row, "bank_raw"].tolist() != ["Slice Small Finance Bank Limited"]:
        raise SystemExit(f"Name fix for {month} rank {rank} no longer matches the raw data")
    banks.loc[row, "bank_raw"] = right_name
    banks.loc[row, "is_name_corrected"] = True

print("Step 3: fixed 2 wrong bank names")
changes.append({"Step": 3, "What we did": "Fixed 2 wrong bank names",
                "Why": "Slice was listed twice while TMB (Mar 2026) and Ujjivan (Jun 2026) were missing", "Rows": 2})


# Step 4: one standard name and a bank type for every spelling
bank_names = pd.read_csv("data/bank_names.csv")
banks = banks.merge(bank_names, on="bank_raw", how="left")

unknown_names = banks[banks["bank"].isna()]["bank_raw"].unique()
if len(unknown_names) > 0:
    raise SystemExit(f"New spelling(s), add them to data/bank_names.csv: {list(unknown_names)}")

print(f"Step 4: {banks['bank_raw'].nunique()} spellings -> {banks['bank'].nunique()} banks")
changes.append({"Step": 4, "What we did": f"One standard name and a type per bank ({banks['bank_raw'].nunique()} spellings -> {banks['bank'].nunique()} banks)",
                "Why": 'NPCI spells banks differently, e.g. "HDFC BANK LTD" and "Hdfc Bank Ltd"',
                "Rows": int((banks["bank_raw"] != banks["bank"]).sum())})


# Step 5: calculated columns
banks["approved_mn"] = banks["total_volume_mn"] * banks["approved_pct"] / 100
banks["bd_failed_mn"] = banks["total_volume_mn"] * banks["bd_pct"] / 100
banks["td_failed_mn"] = banks["total_volume_mn"] * banks["td_pct"] / 100
banks["is_festival_month"] = banks["month"].str[5:].isin(["10", "11"])   # Oct or Nov
banks["above_npci_target"] = banks["td_pct"] > 1.0   # NPCI target: TD below 1%

print("Step 5: added failed-payment counts, festival month, above target")
changes.append({"Step": 5, "What we did": "Added approved_mn, bd_failed_mn, td_failed_mn (= volume x td_pct / 100), is_festival_month, above_npci_target",
                "Why": "Counts are needed to add banks up and to cost failures", "Rows": len(banks)})


# Step 6: average payment value (Rs) from NPCI's vol & val table.
# That table counts approved payments only, so use it only where its volume matches approved_mn within 2%.
raw_values = pd.read_csv("data/raw/npci_member_vol_val.csv", dtype=str)
values = raw_values.drop(columns="month").rename(columns={"file_month": "month", "bank_name": "bank_raw",
                                                          "volume_mn": "vv_volume_mn", "value_cr": "vv_value_cr"})
values = values[["month", "bank_raw", "vv_volume_mn", "vv_value_cr"]]
values["bank_raw"] = values["bank_raw"].str.strip()
values[["vv_volume_mn", "vv_value_cr"]] = values[["vv_volume_mn", "vv_value_cr"]].replace(",", "", regex=True).apply(pd.to_numeric, errors="coerce")
values = values.merge(bank_names[["bank_raw", "bank"]], on="bank_raw")   # also drops "Total" and "Others"
values["avg_payment_value_inr"] = values["vv_value_cr"] * 10 / values["vv_volume_mn"]   # 1 crore = 10 million
values = values[["month", "bank", "vv_volume_mn", "avg_payment_value_inr"]]

banks = banks.merge(values, on=["month", "bank"], how="left")
volumes_match = (banks["vv_volume_mn"] / banks["approved_mn"] - 1).abs() <= 0.02
banks.loc[~volumes_match, "avg_payment_value_inr"] = None
banks = banks.sort_values("avg_payment_value_inr").drop_duplicates(["month", "bank", "rank_in_source"])   # bank listed twice: keep the match
banks["td_failed_value_cr"] = banks["td_failed_mn"] * banks["avg_payment_value_inr"] / 10   # Rs crore

with_value = int(banks["avg_payment_value_inr"].notna().sum())
print(f"Step 6: average payment value for {with_value} bank-months")
changes.append({"Step": 6, "What we did": "Added average payment value (Rs) = value_cr x 10 / volume_mn, and Rs crore of system-failed payments",
                "Why": "Question 4: cost of failures", "Rows": with_value})


# Before vs after for Excel: each raw NPCI row next to the same row after cleaning
after = banks[banks["source"] == "npci_api"].sort_values("npci_row").reset_index(drop=True)
compare = pd.DataFrame({"Month": after["month"], "Rank": after["rank_in_source"].astype(int)})
red_cells = pd.DataFrame()   # True where a value really changed
pairs = [
    ("upi_remitter_banks", "bank", "Bank"),
    ("total_volume_in_mn", "total_volume_mn", "Volume (mn)"),
    ("approved_percent", "approved_pct", "Approved %"),
    ("bd_percent", "bd_pct", "BD %"),
    ("td_percent", "td_pct", "TD %"),
    ("total_debit_reversal_count_in_mn", "debit_reversal_count_mn", "Debit reversals (mn)"),
    ("debit_reversal_success_percent", "debit_reversal_success_pct", "Refund success %"),
]
for raw_column, clean_column, label in pairs:
    compare[label + " (NPCI)"] = raw[raw_column]
    compare[label + " (clean)"] = after[clean_column]
    red_cells[label + " (clean)"] = compare[label + " (NPCI)"].notna() & compare[label + " (clean)"].isna()   # became blank
red_cells["Bank (clean)"] = compare["Bank (NPCI)"] != compare["Bank (clean)"]

compare["What we changed"] = ""
compare.loc[red_cells["Bank (clean)"], "What we changed"] = "Bank name made standard"
compare.loc[after["is_name_corrected"], "What we changed"] = "Wrong bank name fixed (NPCI listed Slice twice)"
compare.loc[red_cells["Debit reversals (mn) (clean)"], "What we changed"] += "; '-' made blank"
compare.loc[red_cells["Refund success % (clean)"], "What we changed"] += "; 'NaN%' made blank"
compare["What we changed"] = compare["What we changed"].str.strip("; ")
red_cells["What we changed"] = compare["What we changed"] != ""


# Fixed column order, sorted by month and rank
banks["rank_in_source"] = banks["rank_in_source"].astype(int)
banks = banks[["month", "bank_raw", "bank", "bank_type", "rank_in_source", "total_volume_mn",
               "approved_pct", "bd_pct", "td_pct", "debit_reversal_count_mn",
               "debit_reversal_success_pct", "approved_mn", "bd_failed_mn", "td_failed_mn",
               "is_festival_month", "above_npci_target", "avg_payment_value_inr",
               "td_failed_value_cr", "udir_auto_update_sr_pct", "udir_refund_sr_pct",
               "source", "is_name_corrected"]]
banks = banks.sort_values(["month", "rank_in_source"]).reset_index(drop=True)


# Step 7: apps, one name per app and its share of all app payments
raw_apps = pd.read_csv("data/raw/npci_apps.csv", dtype=str)
apps = raw_apps.drop(columns="month").rename(columns={"file_month": "month", "total_volume_mn": "volume_mn", "total_value_cr": "value_cr"})
apps["app_raw"] = apps["application_name"].fillna(apps["upi_application_name"])   # NPCI renamed this column
apps["app_raw"] = apps["app_raw"].str.replace("#", "").str.strip()   # "#" is a footnote mark
apps[["volume_mn", "value_cr"]] = apps[["volume_mn", "value_cr"]].replace(",", "", regex=True).apply(pd.to_numeric, errors="coerce")

# Same app, different spelling ("PhonePe" / "Phone Pe"): compare names with only letters, no "limited",
# then use NPCI's latest spelling
apps["app_key"] = apps["app_raw"].str.lower().str.replace("limited", "").str.replace(r"[^a-z]", "", regex=True)
latest_spelling = apps.sort_values("month").groupby("app_key")["app_raw"].last()
apps["app"] = apps["app_key"].map(latest_spelling)

apps["app_share_pct"] = apps["volume_mn"] / apps.groupby("month")["volume_mn"].transform("sum") * 100
apps = apps.sort_values(["month", "volume_mn"], ascending=[True, False])
app_names = apps.groupby(["app_raw", "app"]).size().reset_index(name="Rows")
apps = apps[["month", "app", "volume_mn", "value_cr", "app_share_pct"]].reset_index(drop=True)

print(f"Step 7: {apps['app'].nunique()} apps")
changes.append({"Step": 7, "What we did": f"Apps: removed '#', one name per app ({apps['app'].nunique()} apps), added share %",
                "Why": "Supporting chart on app market share", "Rows": len(apps)})


# Step 8: person-to-person (P2P) vs shop/checkout (P2M) payments
raw_p2p = pd.read_csv("data/raw/npci_p2p_p2m.csv", dtype=str)
p2p = raw_p2p.drop(columns="month").rename(columns={"file_month": "month",
                                                    "p_2_p_volume_mn": "p2p_volume_mn", "p_2_p_value_cr": "p2p_value_cr",
                                                    "p_2_m_volume_mn": "p2m_volume_mn", "p_2_m_value_cr": "p2m_value_cr"})
p2p_numbers = ["p2p_volume_mn", "p2p_value_cr", "p2m_volume_mn", "p2m_value_cr", "total_volume_mn"]
p2p = p2p[["month"] + p2p_numbers]
p2p[p2p_numbers] = p2p[p2p_numbers].replace(",", "", regex=True).apply(pd.to_numeric, errors="coerce")
p2p["p2m_share_pct"] = p2p["p2m_volume_mn"] / (p2p["p2p_volume_mn"] + p2p["p2m_volume_mn"]) * 100
p2p = p2p.sort_values("month").reset_index(drop=True)

print("Step 8: P2P/P2M, added merchant share %")
changes.append({"Step": 8, "What we did": "P2P/P2M: text to numbers, added the merchant (P2M) share %",
                "Why": "Question 5: checkout payments put at risk", "Rows": len(p2p)})


# Checks: the script stops if any fail
total_pct = banks["approved_pct"] + banks["bd_pct"] + banks["td_pct"]
if ((total_pct - 100).abs() > 0.05).any():
    raise SystemExit(f"Approved + BD + TD is not 100:\n{banks[(total_pct - 100).abs() > 0.05]}")

if banks.duplicated(["month", "bank"]).any():
    raise SystemExit(f"Bank listed twice in a month:\n{banks[banks.duplicated(['month', 'bank'], keep=False)]}")

all_months = pd.Series(pd.period_range("2021-08", banks["month"].max(), freq="M").astype(str))
missing_months = all_months[~all_months.isin(banks["month"])]
if len(missing_months) > 0:
    raise SystemExit(f"Missing months: {list(missing_months)}")

banks_per_month = banks.groupby("month").size()
if (banks_per_month != 50).any():
    raise SystemExit(f"Months without 50 banks:\n{banks_per_month[banks_per_month != 50]}")

gap = (p2p["p2p_volume_mn"] + p2p["p2m_volume_mn"] - p2p["total_volume_mn"]).abs()
if (gap > 1).any():
    raise SystemExit(f"P2P + P2M is not equal to the total:\n{p2p[gap > 1]}")

print("All checks passed: rows add to 100%, no duplicates, no missing months, 50 banks every month")


# Save
banks.to_csv("data/clean/upi_bank_monthly.csv", index=False)
apps.to_csv("data/clean/upi_app_monthly.csv", index=False)
p2p.to_csv("data/clean/upi_p2p_p2m_monthly.csv", index=False)

bank_name_list = banks.groupby(["bank_raw", "bank", "bank_type"]).size().reset_index(name="Rows")
red = PatternFill(fill_type="solid", start_color="FFC7CE")   # Excel's light red

with pd.ExcelWriter("excel/upi_clean_data.xlsx") as excel:
    compare.to_excel(excel, sheet_name="Before vs after", index=False)
    pd.DataFrame(changes).to_excel(excel, sheet_name="Changes made", index=False)
    bank_name_list.to_excel(excel, sheet_name="Bank names", index=False)
    app_names.to_excel(excel, sheet_name="App names", index=False)
    banks.to_excel(excel, sheet_name="Clean banks", index=False)
    apps.to_excel(excel, sheet_name="Clean apps", index=False)
    p2p.to_excel(excel, sheet_name="Clean P2P P2M", index=False)

    # Red cell wherever a value really changed (row 1 is the header, so data starts on row 2)
    sheet = excel.sheets["Before vs after"]
    for column in red_cells.columns:
        column_number = compare.columns.get_loc(column) + 1
        for row in red_cells.index[red_cells[column]]:
            sheet.cell(row=row + 2, column=column_number).fill = red

    # Readable column widths and a frozen header row
    for sheet in excel.sheets.values():
        sheet.freeze_panes = "A2"
        for column in sheet.columns:
            sheet.column_dimensions[column[0].column_letter].width = 22
    excel.sheets["Before vs after"].column_dimensions["C"].width = 40
    excel.sheets["Before vs after"].column_dimensions["D"].width = 35
    excel.sheets["Before vs after"].column_dimensions["Q"].width = 50
    excel.sheets["Changes made"].column_dimensions["B"].width = 100
    excel.sheets["Changes made"].column_dimensions["C"].width = 80

print("Saved data/clean/ and excel/upi_clean_data.xlsx")
