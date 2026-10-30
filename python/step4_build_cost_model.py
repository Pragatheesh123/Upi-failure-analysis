# STEP 4: BUILD THE EXCEL COST MODEL
# What if every bank kept system failures (TD) at or below a target? How many payments and Rs would that save?
# Numbers come from SQL (sql/10_cost_model_inputs.sql saves 2 CSV files). This script only writes them into
# Excel and adds formulas, so anyone can click a cell and see how it is worked out.
# Run: python python/step4_build_cost_model.py   (after sql/10)

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.formatting.rule import CellIsRule

yearly = pd.read_csv("excel/cost_model_yearly.csv")
banks = pd.read_csv("excel/cost_model_banks.csv")

yellow = PatternFill("solid", fgColor="FFF2CC")   # cell you can change
red = PatternFill("solid", fgColor="FFC7CE")      # above the target
green = PatternFill("solid", fgColor="C6EFCE")    # at or below the target
bold = Font(bold=True)
grey = Font(italic=True, color="808080")

book = Workbook()


# ---------- Sheet 1: per year ----------
sheet = book.active
sheet.title = "Yearly what-if"
sheet["A1"] = "What if system failures were at most the target? (all top-50 banks, per year)"
sheet["A1"].font = Font(bold=True, size=13)
sheet["A2"] = "Target system fail %"
sheet["B2"] = 1                      # NPCI target: TD below 1%
sheet["B2"].fill = yellow
sheet["C2"] = "<- change this yellow cell (NPCI target = 1). Everything else is a formula."

headers = ["Year", "Payments (mn)", "System-failed payments (mn)", "Avg payment (Rs)", "Checkout share of failures %",
           "System fail %", "Value of failed payments (Rs crore)", "Failed at target (mn)",
           "Payments saved (mn)", "Value saved (Rs crore)", "Checkout payments saved (mn)"]
how = ["", "NPCI data", "NPCI data", "NPCI data (Q6)", "NPCI data (Q6)",
       "= failed / payments x 100", "= failed x avg Rs / 10", "= payments x lower of (fail %, target) / 100",
       "= failed - failed at target", "= saved x avg Rs / 10", "= saved x checkout share / 100"]
for col in range(len(headers)):
    sheet.cell(row=4, column=col + 1, value=headers[col]).font = bold
    sheet.cell(row=5, column=col + 1, value=how[col]).font = grey

row = 6
for year, payments, failed, avg_rs, checkout in yearly.itertuples(index=False):
    sheet[f"A{row}"] = str(year)
    sheet[f"B{row}"] = payments
    sheet[f"C{row}"] = failed
    sheet[f"D{row}"] = avg_rs
    sheet[f"E{row}"] = checkout
    sheet[f"F{row}"] = f"=C{row}/B{row}*100"
    sheet[f"G{row}"] = f"=C{row}*D{row}/10"          # mn payments x Rs = Rs mn; / 10 = Rs crore
    sheet[f"H{row}"] = f"=B{row}*MIN(F{row},$B$2)/100"
    sheet[f"I{row}"] = f"=C{row}-H{row}"
    sheet[f"J{row}"] = f"=I{row}*D{row}/10"
    sheet[f"K{row}"] = f"=I{row}*E{row}/100"
    row = row + 1
last_year_row = row - 1
sheet[f"A{row + 1}"] = "2026 = Jan to Sep only. Value = Rs size of failed attempts, not money lost (most people retry)."
sheet[f"A{row + 1}"].font = grey


# ---------- Sheet 2: per bank, last 12 months ----------
sheet2 = book.create_sheet("Bank what-if")
sheet2["A1"] = "Which banks would gain most from hitting the target? (Oct 2025 to Sep 2026)"
sheet2["A1"].font = Font(bold=True, size=13)
sheet2["A2"] = "Target system fail %"
sheet2["B2"] = "='Yearly what-if'!B2"   # same target as sheet 1
sheet2["C2"] = "<- comes from the yellow cell on the Yearly sheet"

headers = ["Bank", "Bank group", "Payments (mn)", "System-failed payments (mn)", "Avg payment (Rs)",
           "System fail %", "Value of failed payments (Rs crore)", "Failed at target (mn)",
           "Payments saved (mn)", "Value saved (Rs crore)"]
how = ["", "", "NPCI data", "NPCI data", "NPCI data (blank = no match)",
       "= failed / payments x 100", "= failed x avg Rs / 10", "= payments x lower of (fail %, target) / 100",
       "= failed - failed at target", "= saved x avg Rs / 10"]
for col in range(len(headers)):
    sheet2.cell(row=4, column=col + 1, value=headers[col]).font = bold
    sheet2.cell(row=5, column=col + 1, value=how[col]).font = grey

row = 6
for bank, group, payments, failed, avg_rs in banks.itertuples(index=False):
    sheet2[f"A{row}"] = bank
    sheet2[f"B{row}"] = group
    sheet2[f"C{row}"] = payments
    sheet2[f"D{row}"] = failed
    if not pd.isna(avg_rs):              # leave the cell empty when there is no Rs value
        sheet2[f"E{row}"] = avg_rs
    sheet2[f"F{row}"] = f"=D{row}/C{row}*100"
    sheet2[f"G{row}"] = f'=IF(E{row}="","",D{row}*E{row}/10)'
    sheet2[f"H{row}"] = f"=C{row}*MIN(F{row},$B$2)/100"
    sheet2[f"I{row}"] = f"=D{row}-H{row}"
    sheet2[f"J{row}"] = f'=IF(E{row}="","",I{row}*E{row}/10)'
    row = row + 1
last_bank_row = row - 1

# total row
sheet2[f"A{row}"] = "All banks"
sheet2[f"A{row}"].font = bold
for letter in ["C", "D", "G", "H", "I", "J"]:
    sheet2[f"{letter}{row}"] = f"=SUM({letter}6:{letter}{last_bank_row})"
    sheet2[f"{letter}{row}"].font = bold
sheet2[f"F{row}"] = f"=D{row}/C{row}*100"
sheet2[f"A{row + 2}"] = "Rs columns skip banks with no Rs match, so the Rs totals are a little low."
sheet2[f"A{row + 2}"].font = grey

# colour the fail % cells: red above the target, green at or below
sheet2.conditional_formatting.add(f"F6:F{last_bank_row}", CellIsRule(operator="greaterThan", formula=["$B$2"], fill=red))
sheet2.conditional_formatting.add(f"F6:F{last_bank_row}", CellIsRule(operator="lessThanOrEqual", formula=["$B$2"], fill=green))
sheet.conditional_formatting.add(f"F6:F{last_year_row}", CellIsRule(operator="greaterThan", formula=["$B$2"], fill=red))
sheet.conditional_formatting.add(f"F6:F{last_year_row}", CellIsRule(operator="lessThanOrEqual", formula=["$B$2"], fill=green))


# ---------- Sheet 3: notes ----------
notes = book.create_sheet("Notes")
lines = [
    "Where the numbers come from",
    "All numbers come from NPCI's monthly UPI tables (top 50 remitter banks), via data/clean/ and sql/10_cost_model_inputs.sql.",
    "System failure = Technical Decline (TD): the bank's or NPCI's systems failed. Not the user's fault.",
    "Avg payment (Rs) = NPCI value / approved payments, only in months where NPCI's 2 tables agree within 2% (same as Q6).",
    "Checkout share = share of shop (P2M) payments that month, weighted by failures. It is an estimate.",
    "Yearly value uses the average Rs size for ALL failed payments, so it is a bit higher than Q6 (Q6 counts only matched banks).",
    "",
    "What the model does NOT say",
    "Value of failed payments is the Rs size of failed attempts, not money lost: most people retry, and the money is never taken.",
    "We don't know how many people gave up after a failure, so no 'sales lost' number is shown.",
]
for i in range(len(lines)):
    notes[f"A{i + 1}"] = lines[i]
notes["A1"].font = bold
notes["A8"].font = bold


# ---------- Formats and save ----------
for ws in [sheet, sheet2]:
    for cells in ws.iter_rows(min_row=6, min_col=3):
        for cell in cells:
            cell.number_format = "#,##0.00"
    ws.column_dimensions["A"].width = 34
    for letter in "BCDEFGHIJK":
        ws.column_dimensions[letter].width = 20
    ws.freeze_panes = "B6"               # header rows and first column stay on screen while scrolling
sheet2.column_dimensions["B"].width = 16
for cells in sheet.iter_rows(min_row=6, min_col=2, max_col=2):
    for cell in cells:
        cell.number_format = "#,##0.00"
notes.column_dimensions["A"].width = 120

book.save("excel/upi_cost_model.xlsx")
print("Saved excel/upi_cost_model.xlsx:", len(yearly), "years,", len(banks), "banks")
