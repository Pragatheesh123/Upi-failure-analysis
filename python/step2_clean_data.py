# STEP 2: CLEAN THE DATA
#
# Input:  the raw NPCI tables in data/raw/ and the bank name list data/bank_names.csv
# Output: data/clean/upi_bank_monthly.csv, upi_app_monthly.csv, upi_p2p_p2m_monthly.csv
#         excel/upi_clean_data.xlsx  (the same tables + a sheet listing every change made)
#
# Run from the project folder:  python python/step2_clean_data.py
# Nothing is guessed or filled in. If a check fails, the script stops.

import pandas as pd

changes = []  # each step adds one line here; it becomes the "Changes made" sheet in Excel


# =====================================================================
# BANK TABLE
# =====================================================================

# Step 1: read the raw bank table (Jan 2022 to Sep 2026). dtype=str keeps every value as NPCI wrote it.
raw = pd.read_csv("data/raw/npci_remitter.csv", dtype=str)

banks = pd.DataFrame()
banks["month"] = raw["file_month"]
banks["bank_raw"] = raw["upi_remitter_banks"].str.strip()   # some names had extra spaces or line breaks
banks["rank_in_source"] = raw["sr_no"]
banks["total_volume_mn"] = raw["total_volume_in_mn"]
banks["approved_pct"] = raw["approved_percent"]
banks["bd_pct"] = raw["bd_percent"]
banks["td_pct"] = raw["td_percent"]
banks["debit_reversal_count_mn"] = raw["total_debit_reversal_count_in_mn"]
banks["debit_reversal_success_pct"] = raw["debit_reversal_success_percent"]
banks["udir_auto_update_sr_pct"] = raw["udir_auto_update_sr_percent"]
banks["udir_refund_sr_pct"] = raw["udir_refund_sr_percent"]
banks["source"] = "npci_api"

# NPCI writes numbers as text, like "7,47,792.52" or "90.34%": remove , and % and turn them into numbers.
# Anything that still isn't a number (like "-") becomes blank, never a guess.
number_columns = ["rank_in_source", "total_volume_mn", "approved_pct", "bd_pct", "td_pct",
                  "debit_reversal_count_mn", "debit_reversal_success_pct",
                  "udir_auto_update_sr_pct", "udir_refund_sr_pct"]
for column in number_columns:
    text = banks[column].str.replace(",", "").str.replace("%", "").str.strip()
    banks[column] = pd.to_numeric(text, errors="coerce")

print(f"Step 1: read {len(banks)} bank rows and turned text into numbers")
changes.append({"Step": 1, "What we did": "Read the raw bank table and turned text into numbers",
                "Why": "NPCI writes numbers as text, like 90.34%", "Rows": len(banks),
                "Example": f'"{raw["approved_percent"][0]}" -> {banks["approved_pct"][0]}'})


# Step 2: add Aug-Dec 2021 from the earlier archive copy (marked provisional)
old = pd.read_csv("data/raw/npci_archive_2021_remitter_provisional.csv")
old = old[old["month"] >= "2021-08"]   # top 50 banks start in Aug 2021; Mar-Jul 2021 was top 30
old["bank_raw"] = old["bank_raw"].str.strip()
old["source"] = "npci_archive_2021_provisional"
banks = pd.concat([old, banks], ignore_index=True)

print(f"Step 2: added {len(old)} rows for Aug-Dec 2021")
changes.append({"Step": 2, "What we did": "Added Aug-Dec 2021 from the NPCI archive copy, marked provisional",
                "Why": "The data feed starts in Jan 2022; 2021 adds one more festival season",
                "Rows": len(old), "Example": "source = npci_archive_2021_provisional"})


# Step 3: fix 2 rows where NPCI printed the wrong bank name.
# In Mar and Jun 2026 "Slice" is listed twice and one bank is missing. The extra row's volume,
# approval % and rank match the missing bank in the months before and after. Only the name changes.
banks["is_name_corrected"] = False

row = (banks["month"] == "2026-03") & (banks["rank_in_source"] == 36)
if banks.loc[row, "bank_raw"].tolist() != ["Slice Small Finance Bank Limited"]:
    raise SystemExit("Name fix for Mar 2026 rank 36 no longer matches the raw data")
banks.loc[row, "bank_raw"] = "Tamilnad Mercantile Bank Limited"
banks.loc[row, "is_name_corrected"] = True

row = (banks["month"] == "2026-06") & (banks["rank_in_source"] == 38)
if banks.loc[row, "bank_raw"].tolist() != ["Slice Small Finance Bank Limited"]:
    raise SystemExit("Name fix for Jun 2026 rank 38 no longer matches the raw data")
banks.loc[row, "bank_raw"] = "Ujjivan Small Finance Bank Limited"
banks.loc[row, "is_name_corrected"] = True

print("Step 3: fixed 2 wrong bank names from NPCI")
changes.append({"Step": 3, "What we did": "Fixed 2 rows where NPCI printed the wrong bank name",
                "Why": "Slice was listed twice while TMB (Mar 2026) and Ujjivan (Jun 2026) were missing",
                "Rows": 2, "Example": "Mar 2026 rank 36: Slice -> Tamilnad Mercantile Bank"})


# Step 4: one standard name and a bank type for every spelling, from data/bank_names.csv
bank_names = pd.read_csv("data/bank_names.csv")
banks = banks.merge(bank_names, on="bank_raw", how="left")

unknown_names = banks[banks["bank"].isna()]["bank_raw"].unique()
if len(unknown_names) > 0:
    raise SystemExit(f"New spelling(s), add them to data/bank_names.csv: {list(unknown_names)}")

spellings = banks["bank_raw"].nunique()
print(f"Step 4: {spellings} spellings -> {banks['bank'].nunique()} banks, each with a bank type")
changes.append({"Step": 4, "What we did": f"Gave every bank one standard name and a type ({spellings} spellings -> {banks['bank'].nunique()} banks)",
                "Why": "NPCI spells the same bank differently across months",
                "Rows": int((banks["bank_raw"] != banks["bank"]).sum()),
                "Example": '"HDFC BANK LTD." and "Hdfc Bank Ltd" -> "HDFC Bank", type Private'})


# Step 5: calculated columns
banks["approved_mn"] = banks["total_volume_mn"] * banks["approved_pct"] / 100
banks["bd_failed_mn"] = banks["total_volume_mn"] * banks["bd_pct"] / 100
banks["td_failed_mn"] = banks["total_volume_mn"] * banks["td_pct"] / 100
banks["is_festival_month"] = banks["month"].str[5:].isin(["10", "11"])   # October or November
banks["above_npci_target"] = banks["td_pct"] > 1.0   # NPCI target: TD below 1% (circular OC 149A)

print("Step 5: added failed-payment counts, festival month and above-target columns")
changes.append({"Step": 5, "What we did": "Added approved_mn, bd_failed_mn, td_failed_mn, is_festival_month, above_npci_target",
                "Why": "Counts (not just %) are needed to add banks up and to cost failures",
                "Rows": len(banks), "Example": "td_failed_mn = total_volume_mn x td_pct / 100"})


# Step 6: average payment value (Rs) per bank, from NPCI's "Top 50 Member Vol & Val" table.
# That table counts approved payments only, so a bank's value is used only when its volume matches
# our approved_mn within 2%. Some months in it have banks swapped (e.g. Axis and Yes, early 2023).
raw_values = pd.read_csv("data/raw/npci_member_vol_val.csv", dtype=str)

values = pd.DataFrame()
values["month"] = raw_values["file_month"]
values["bank_raw"] = raw_values["bank_name"].str.strip()
values["vv_volume_mn"] = pd.to_numeric(raw_values["volume_mn"].str.replace(",", ""), errors="coerce")
values["vv_value_cr"] = pd.to_numeric(raw_values["value_cr"].str.replace(",", ""), errors="coerce")
values = values.merge(bank_names[["bank_raw", "bank"]], on="bank_raw")   # also drops the "Total" and "Others" rows
values["avg_payment_value_inr"] = values["vv_value_cr"] * 10 / values["vv_volume_mn"]   # 1 crore = 10 million
values = values[["month", "bank", "vv_volume_mn", "avg_payment_value_inr"]]

banks = banks.merge(values, on=["month", "bank"], how="left")
volumes_match = (banks["vv_volume_mn"] / banks["approved_mn"] - 1).abs() <= 0.02
banks.loc[~volumes_match, "avg_payment_value_inr"] = None
# A bank listed twice in that table gives two rows here: keep the one whose volume matched
banks = banks.sort_values("avg_payment_value_inr").drop_duplicates(["month", "bank", "rank_in_source"])
banks["td_failed_value_cr"] = banks["td_failed_mn"] * banks["avg_payment_value_inr"] / 10   # Rs crore

with_value = int(banks["avg_payment_value_inr"].notna().sum())
print(f"Step 6: added average payment value for {with_value} bank-months")
changes.append({"Step": 6, "What we did": "Added average payment value (Rs) and Rs crore value of system-failed payments",
                "Why": "Question 4: cost of failures. Used only where both NPCI tables agree",
                "Rows": with_value, "Example": "avg_payment_value_inr = value_cr x 10 / volume_mn"})


# Fixed column order, sorted by month and rank
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

# Step 7: one row per app per month, with its share of all app payments
raw_apps = pd.read_csv("data/raw/npci_apps.csv", dtype=str)

apps = pd.DataFrame()
apps["month"] = raw_apps["file_month"]
# NPCI renamed the column in later months, so take whichever one has the name
apps["app_raw"] = raw_apps["application_name"].fillna(raw_apps["upi_application_name"])
apps["app_raw"] = apps["app_raw"].str.replace("#", "").str.strip()   # "#" is a footnote mark, not part of the name
apps["volume_mn"] = pd.to_numeric(raw_apps["total_volume_mn"].str.replace(",", ""), errors="coerce")
apps["value_cr"] = pd.to_numeric(raw_apps["total_value_cr"].str.replace(",", ""), errors="coerce")

# Same app, different spelling ("PhonePe" / "Phone Pe", "... Digital" / "... Digital Limited"):
# compare names without case, spaces, dots or "limited", then use the spelling NPCI used most recently
apps["app_key"] = apps["app_raw"].str.lower().str.replace("limited", "").str.replace(r"[^a-z]", "", regex=True)
latest_spelling = apps.sort_values("month").groupby("app_key")["app_raw"].last()
apps["app"] = apps["app_key"].map(latest_spelling)

apps["app_share_pct"] = apps["volume_mn"] / apps.groupby("month")["volume_mn"].transform("sum") * 100
apps = apps.sort_values(["month", "volume_mn"], ascending=[True, False])
apps = apps[["month", "app", "volume_mn", "value_cr", "app_share_pct"]].reset_index(drop=True)

print(f"Step 7: apps cleaned, {apps['app'].nunique()} apps")
changes.append({"Step": 7, "What we did": f"Apps: removed footnote marks, one name per app ({apps['app'].nunique()} apps), added share %",
                "Why": "Supporting chart on app market share", "Rows": len(apps),
                "Example": '"Phone Pe #" -> "Phone Pe"'})


# =====================================================================
# P2P / P2M TABLE
# =====================================================================

# Step 8: person-to-person (P2P) vs person-to-merchant (P2M = shop/checkout) payments per month
raw_p2p = pd.read_csv("data/raw/npci_p2p_p2m.csv", dtype=str)

p2p = pd.DataFrame()
p2p["month"] = raw_p2p["file_month"]
p2p["p2p_volume_mn"] = raw_p2p["p_2_p_volume_mn"]
p2p["p2p_value_cr"] = raw_p2p["p_2_p_value_cr"]
p2p["p2m_volume_mn"] = raw_p2p["p_2_m_volume_mn"]
p2p["p2m_value_cr"] = raw_p2p["p_2_m_value_cr"]
p2p["total_volume_mn"] = raw_p2p["total_volume_mn"]
for column in ["p2p_volume_mn", "p2p_value_cr", "p2m_volume_mn", "p2m_value_cr", "total_volume_mn"]:
    p2p[column] = pd.to_numeric(p2p[column].str.replace(",", ""), errors="coerce")
p2p["p2m_share_pct"] = p2p["p2m_volume_mn"] / (p2p["p2p_volume_mn"] + p2p["p2m_volume_mn"]) * 100
p2p = p2p.sort_values("month").reset_index(drop=True)

print("Step 8: P2P/P2M cleaned, added the merchant (P2M) share %")
changes.append({"Step": 8, "What we did": "P2P/P2M: turned text into numbers and added the merchant (P2M) share %",
                "Why": "Question 5: how many checkout payments were put at risk", "Rows": len(p2p),
                "Example": f'"{raw_p2p["p_2_m_volume_mn"].iloc[-1]}" -> {p2p["p2m_volume_mn"].iloc[-1]}'})


# =====================================================================
# CHECKS - the script stops if any of these fail
# =====================================================================

# Check 1: Approved + BD + TD must add up to 100% (0.05 allowed for rounding)
total_pct = banks["approved_pct"] + banks["bd_pct"] + banks["td_pct"]
if ((total_pct - 100).abs() > 0.05).any():
    raise SystemExit(f"Approved + BD + TD is not 100 on these rows:\n{banks[(total_pct - 100).abs() > 0.05]}")

# Check 2: each bank only once per month
if banks.duplicated(["month", "bank"]).any():
    raise SystemExit(f"Bank listed twice in a month:\n{banks[banks.duplicated(['month', 'bank'], keep=False)]}")

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

print("All checks passed: rows add to 100%, no duplicates, no missing months, 50 banks every month")


# =====================================================================
# SAVE
# =====================================================================

banks.to_csv("data/clean/upi_bank_monthly.csv", index=False)
apps.to_csv("data/clean/upi_app_monthly.csv", index=False)
p2p.to_csv("data/clean/upi_p2p_p2m_monthly.csv", index=False)

# Excel copy to look at: the changes first, then the bank-name list, then the clean tables
names_used = banks.groupby(["bank_raw", "bank", "bank_type"]).size().reset_index(name="rows")
with pd.ExcelWriter("excel/upi_clean_data.xlsx") as excel:
    pd.DataFrame(changes).to_excel(excel, sheet_name="Changes made", index=False)
    names_used.to_excel(excel, sheet_name="Bank names", index=False)
    banks.to_excel(excel, sheet_name="Banks", index=False)
    apps.to_excel(excel, sheet_name="Apps", index=False)
    p2p.to_excel(excel, sheet_name="P2P P2M", index=False)
    # Make the columns wide enough to read
    for sheet in excel.sheets.values():
        for column in sheet.columns:
            width = max(len(str(cell.value or "")) for cell in column[:200])
            sheet.column_dimensions[column[0].column_letter].width = min(width + 2, 60)

print(f"Saved data/clean/ (banks {len(banks)}, apps {len(apps)}, P2P/P2M {len(p2p)} rows) and excel/upi_clean_data.xlsx")
