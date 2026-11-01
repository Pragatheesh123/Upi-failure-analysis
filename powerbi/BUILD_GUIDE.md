# Power BI build guide (about 1 hour)

Two pages: **1. Overview & bank scorecard**, **2. Bank type report**.
Data: `powerbi/data/bank_details.csv` (made by `sql/11_powerbi_export.sql`). Every calculated column already comes from SQL; Power BI only adds things up.

Colours: navy `#1F3A5F` for normal, red `#C0392B` above target, green `#2E8B57` within target.

---

## Step 1. Load the data (5 min)

1. Open Power BI Desktop → **Get data → Text/CSV** → pick `powerbi/data/bank_details.csv` → **Transform Data**.
2. In Power Query, check the column types (icon left of each header):
   - `month`, `bank`, `bank_group`, `bank_type`, `year` → **Text** (ABC)
   - `total_volume_mn`, `system_failed_mn`, `user_failed_mn`, `td_pct`, `bd_pct`, `debit_reversal_count_mn`, `debit_reversal_success_pct` → **Decimal number** (1.2)
3. Add a real date (charts need it for a time axis): **Add Column → Custom Column**
   - Name: `month_date`
   - Formula: `Date.FromText([month] & "-01")` ("2025-10" becomes 1 Oct 2025)
   - Then set its type to **Date**.
4. **Close & Apply**.
5. **View → Themes → Browse for themes** → pick `powerbi/upi_theme.json`.

## Step 2. Measures (15 min)

A **measure** is a formula that is worked out again for whatever you are looking at (a year, a bank, a group). Click the table in the Data pane → **New measure**, paste one at a time.

```DAX
Payments (mn) = SUM ( bank_details[total_volume_mn] )
```
Adds up all payments in the current view.

```DAX
System failed (mn) = SUM ( bank_details[system_failed_mn] )
```

```DAX
User failed (mn) = SUM ( bank_details[user_failed_mn] )
```

```DAX
System fail % = DIVIDE ( [System failed (mn)], [Payments (mn)] ) * 100
```
Total failed ÷ total payments (volume-weighted, same as the SQL). `DIVIDE` returns blank instead of an error when payments are 0.

```DAX
User fail % = DIVIDE ( [User failed (mn)], [Payments (mn)] ) * 100
```

```DAX
Refund success % =
DIVIDE (
    SUMX ( bank_details, bank_details[debit_reversal_count_mn] * bank_details[debit_reversal_success_pct] / 100 ),
    CALCULATE ( SUM ( bank_details[debit_reversal_count_mn] ), NOT ISBLANK ( bank_details[debit_reversal_success_pct] ) )
) * 100
```
Top line: refunds that worked. `SUMX` goes row by row (refunds needed × success %) and adds up. Rows with no success % give blank and are skipped.
Bottom line: refunds needed, only rows where NPCI gave a success % (`CALCULATE` = SUM with a filter). Same as `sql/07`.

```DAX
Banks = DISTINCTCOUNT ( bank_details[bank] )
```
How many different banks are in the view (show it next to every group number).

```DAX
Months above 1% = COUNTROWS ( FILTER ( bank_details, bank_details[td_pct] > 1 ) )
```
How many bank-months had system failures above the NPCI target. Near 12 in a year = steady problem.

```DAX
System fail colour = IF ( [System fail %] > 1, "#C0392B", "#2E8B57" )
```
Red above the 1% target, green within. Used for conditional formatting below.

Check: make a quick table with `year` and `System fail %`. It must show 1.55, 1.45, 1.01, 0.59, 0.40, 0.26 (same as `sql/03`). Then delete the table.

## Step 3. Page 1: Overview & bank scorecard (20 min)

Rename the page "Overview".

1. **Slicers** (top row): `year` and `bank_group`. Format → Slicer settings → Style: **Dropdown**.
2. **4 cards** (Card visual): `Payments (mn)`, `System fail %`, `User fail %`, `Refund success %`. Format → Callout value → decimal places 2.
3. **Line chart 1**: X-axis `month_date`, Y-axis `System fail %`. Analytics pane (magnifier icon) → **Constant line** = 1, label "NPCI target 1%".
4. **Line chart 2**: X-axis `month_date`, Y-axis `User fail %`, constant line = 5 ("NPCI target 5%"). Two charts, not one with two axes: the scales are too different (0–2 vs 0–11).
5. **Table (bank scorecard)**: `bank`, `bank_group`, `Payments (mn)`, `System fail %`, `User fail %`, `Refund success %`, `Months above 1%`.
   - Sort by `System fail %` (click the header, highest first).
   - Colour: in the Visualizations pane, right-click `System fail %` in the Columns list → **Conditional formatting → Background color** → Format style **Field value** → field `System fail colour`.
6. Title text box: "Where does UPI fail? Top 50 banks, Aug 2021 – Sep 2026".

## Step 4. Page 2: Bank type report (15 min)

New page, name it "Bank types". Add the `year` slicer again (or Sync slicers from page 1: View → Sync slicers).

1. **Bar chart**: Y-axis `bank_group`, X-axis `System fail %`. Format → Bars → Colors → **fx** → Field value → `System fail colour`. Constant line = 1.
2. **Bar chart**: Y-axis `bank_group`, X-axis `Refund success %`.
3. **Matrix**: Rows `bank_group`, Columns `year`, Values `System fail %` and `Banks`. Conditional formatting on `System fail %` → Background color → Field value → `System fail colour`.
4. **Text box** with the finding: "Gramin banks are hit twice: 1.95% system failures (more than 4x the next group) and only 57% of refunds succeed (85–92% elsewhere). Last 12 months."
   Check: with year slicer empty and a filter `month_date` ≥ 1 Oct 2025, the bars must show Gramin 1.95 and 57.09 (same as `sql/06` and `sql/07`).

## Step 5. Save and share (5 min)

1. **File → Save as** `powerbi/upi_failure_dashboard.pbix`.
2. Screenshot each page (Win + Shift + S) → save as `images/powerbi_overview.png` and `images/powerbi_bank_types.png`.
3. Put the screenshots into the README, then commit and push.

## Interview answers you should be able to give
- **Why a measure and not a column?** A measure is recalculated for each filter (year, bank, group). A % column added up would be wrong: you can't add percentages.
- **Why `DIVIDE` and not `/`?** It gives blank instead of an error when the bottom number is 0.
- **What does `CALCULATE` do?** Runs a calculation with an extra filter, here "only rows that have a refund %".
- **What does `SUMX` do?** Works row by row, then adds up. Needed because refunds that worked = count × % for each row first.
