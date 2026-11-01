# Power BI build guide (round 4: 4 pages, What → Why → Where → Cost and action)

> **The finished dashboard is already in this folder:** open `UPI Failure Dashboard.pbip` in Power BI Desktop and click **Refresh**. It reads the CSV files in `powerbi/data/` (made by `sql/11_powerbi_export.sql`) by the path `D:\upi failure\powerbi\data\`; if you move the project, change the path in **Transform data**.
> Use this guide to explain each part in an interview, or to rebuild it yourself for practice.

**Words used on the dashboard** (the measure names inside the model can stay as they are; only the labels on the visuals change):

| Thing | Shown as | Never call it |
|---|---|---|
| TD (technical decline) | **System failure %** (bank side or NPCI side) | "the bank's fault" |
| BD (business decline) | **Decline %**: a wrong PIN, low balance, or a limit set by the bank | "user failures" |
| Debit reversal success % | **Automatic refund %** | "refund success", "money lost" |
| A change in a rate | **pts** (percentage points) | "%" |

**The rule for every page:** one title that states the finding, one sentence that says what it means, one main chart that proves it.

---

## 1. Tables (Model view)

| Table | From | What it holds |
|---|---|---|
| `bank_details` | `powerbi/data/bank_details.csv` | One row per bank per month, with every calculated column from `sql/02` (system_failed_mn, user_failed_mn, bank_group, `gramin_or_other`, `year_label`) plus `month_date` (added in Power Query: `Date.FromText([month] & "-01")`) |
| `events` | `events.csv` | Dated NPCI / RBI events (month, event, source). **No relationship**: measures connect it with `TREATAS` |
| `why_split` | `why_split.csv` | The rate vs mix split for 3 changes |
| `cost_by_year` | `cost_by_year.csv` | System-failed and checkout payments per year |
| `bank_last_12_months` | `bank_last_12_months.csv` | Each bank's last 12 months: payments, system-failed, avg payment in Rs |
| `Target TD %` | **What-if parameter** (Modeling → New parameter → Numeric range: 0.25 to 2, step 0.25, default 1) | Feeds the slider on page 4 |

**Sort by column:** `year_label` ("2021 (Aug-Dec)" … "2026 (Jan-Sep)") is sorted by `year` (select the column → Column tools → Sort by column → year), otherwise the labels sort alphabetically. `why_split[change]` is sorted by `step`.

## 2. Measures, in plain words

### Basic (table `bank_details`)
```DAX
Payments (mn) = SUM(bank_details[total_volume_mn])
System failed (mn) = SUM(bank_details[system_failed_mn])
User failed (mn) = SUM(bank_details[user_failed_mn])              -- shown as "declines"
System fail % = DIVIDE([System failed (mn)], [Payments (mn)]) * 100
User fail % = DIVIDE([User failed (mn)], [Payments (mn)]) * 100   -- shown as "Decline %"
Refund success % =                                                 -- shown as "Automatic refund %"
DIVIDE(
    SUMX(bank_details, bank_details[debit_reversal_count_mn] * bank_details[debit_reversal_success_pct] / 100),
    CALCULATE(SUM(bank_details[debit_reversal_count_mn]), NOT ISBLANK(bank_details[debit_reversal_success_pct]))
) * 100
```
- **Why total ÷ total:** a rate for many banks must be weighted by size (volume-weighted). Averaging percentages would let a tiny bank count as much as SBI.
- **`DIVIDE`** gives blank instead of an error when the bottom number is 0.
- **`SUMX`** works row by row (refunds needed × success % for each bank-month), then adds up.
- **`CALCULATE`** means the same calculation with an extra filter: here, only rows that have a refund %.

### Last 12 months and 2022 (the cards)
```DAX
Latest month = CALCULATE(MAX(bank_details[month_date]), ALL(bank_details))
System fail % (last 12 months) =
VAR start_date = EDATE([Latest month], -12)
RETURN CALCULATE([System fail %], bank_details[month_date] > start_date)
System fail % 2022 = CALCULATE([System fail %], bank_details[year] = "2022")
System failure note = "2022: " & FORMAT([System fail % 2022], "0.00") & "% · target below 1%"
```
- **Latest month** is the newest month in the whole table. `ALL` means "ignore every filter".
- **`VAR`** stores the start date first, because a `CALCULATE` filter can't use a measure directly.
- The same pattern gives `Payments (bn, last 12 months)`, `User fail % (last 12 months)`, `Refund success % (last 12 months)` and the matching `… 2022` measures and notes. The notes are text measures (`&` joins text, `FORMAT` turns a number into text), so the "2022: …" lines under the cards are worked out, not typed.
- **Why fixed to the last 12 months:** the title says "nearly 10%", so the cards must use the same window. An all-time average (7.55%) would contradict it. That's why page 1 has no Year slicer.

### Colours (conditional formatting by field value)
```DAX
Last 12 months colour = IF([System fail % (last 12 months)] > 1, "#C0392B", "#2E8B57")   -- red above 1%, green within
Refund bar colour = IF(SELECTEDVALUE(bank_details[bank_group]) = "Gramin", "#C0392B", "#1F3A5F")
```
`SELECTEDVALUE` returns the bank group of the current bar.

### Page 1: share of failures caused by systems
```DAX
System share of failures % = DIVIDE([System failed (mn)], [System failed (mn)] + [User failed (mn)]) * 100
```
Of all failed payments, how many were system failures: 18.6% in 2021 → 2.5% in 2026.

### Page 2: where payments moved, and event markers
```DAX
Share India Post + Airtel % =
COALESCE(DIVIDE(
    CALCULATE([Payments (mn)], bank_details[bank] IN {"India Post Payments Bank", "Airtel Payments Bank"}),
    CALCULATE([Payments (mn)], REMOVEFILTERS(bank_details[bank], bank_details[bank_group], bank_details[bank_type]))
) * 100, 0)
Event marker (BD %) = IF(CALCULATE(COUNTROWS(events), TREATAS(VALUES(bank_details[month]), events[month])) > 0, [User fail %])
Event text = CALCULATE(SELECTEDVALUE(events[event]), TREATAS(VALUES(bank_details[month]), events[month]))
```
- **Top line:** payments at the two banks. **Bottom line:** all payments; `REMOVEFILTERS` means "ignore which bank you're looking at". `COALESCE(…, 0)` shows 0 instead of blank after Paytm left.
- **`TREATAS`** says "use this month list as if it were the events table's months". So the marker only has a value in months with an event, and the chart draws a dot only there. `Event text` and `Event source` go in the chart's **Tooltips** box, so hovering a dot shows the event and its source.
- The `why_split` cards: `Rate effect, system failure 2022-2025 (pts) = CALCULATE(SUM(why_split[from_banks_themselves]), why_split[step] = 1)`, and the same idea for the other two.

### Page 4: the slider, avoidable failures, top 5
```DAX
Target TD % Value = SELECTEDVALUE('Target TD %'[Target TD %], 1)   -- what the slider is set to (1 if nothing is picked)
Avoidable at target (mn) =
SUMX(bank_last_12_months,
     MAX(0, bank_last_12_months[system_failed_mn] - bank_last_12_months[payments_mn] * [Target TD % Value] / 100))
Avoidable value at target (Rs crore, estimate) =
SUMX(bank_last_12_months,
     MAX(0, bank_last_12_months[system_failed_mn] - bank_last_12_months[payments_mn] * [Target TD % Value] / 100)
         * bank_last_12_months[avg_payment_rs] / 10)      -- mn payments x Rs = Rs mn; / 10 = Rs crore
Avoidable share of payments % = DIVIDE([Avoidable at target (mn)], SUM(bank_last_12_months[payments_mn])) * 100
Avoidable at 3 Gramin banks (mn) =
CALCULATE([Avoidable at target (mn)],
          bank_last_12_months[bank] IN {"Uttar Pradesh Gramin Bank", "Rajasthan Gramin Bank", "Telangana Grameena Bank"})
Share at 3 Gramin banks % = DIVIDE([Avoidable at 3 Gramin banks (mn)], [Avoidable at target (mn)]) * 100
Avoidable top 5 (mn) = IF(RANKX(ALL(bank_last_12_months[bank]), [Avoidable at target (mn)]) <= 5, [Avoidable at target (mn)])
```
- **Avoidable:** for each bank, its failed payments above the target, or 0 if it's already within (`MAX(0, …)`). Then add up the banks (`SUMX`).
- **The 3 banks are a fixed list**, the 3 biggest at the 1% target. It's a fixed list on purpose: the recommendation names these 3 banks, so the card must show these 3 even when the slider moves.
- **Slider note:** `Target note = "Now: " & FORMAT([Target TD % Value], "0.00") & "% · drag 0.25% to 2%"` sits under the slider, so the target in use is always visible (before anyone drags it, the slider box shows its lowest value but the measures use the default 1%).
- **Top 5:** `RANKX` ranks every bank by avoidable payments. Banks ranked 6th or lower get blank, and blank bars are not drawn. This does the same job as a Top N filter, but it's visible in a formula you can explain.

## 3. Click steps for the new parts

- **Page navigator** (buttons "1 What · 2 Why · 3 Where · 4 Cost and action"):
  1. Rename the pages: double-click each tab.
  2. Insert → Buttons → Navigator → **Page navigator**.
  3. Format → Style → State **Selected** → Fill navy, text white.
  4. In Desktop, Ctrl + click a button to jump.
- **Rename for this visual:** in the Visualizations pane, double-click a field (or right-click → Rename for this visual). This changes the label on that visual only, e.g. `User fail %` → "Decline %". The measure name in the model stays the same.
- **Data bars** (scorecard, System failed column): Format → Cell elements → pick the column → Data bars on.
- **Red/green cells and bars:** Format → Cell elements (table) or Bars → Colors → **fx** → Format style **Field value** → pick the colour measure.
- **What-if parameter (slider):**
  1. Modeling → New parameter → Numeric range.
  2. Name it "Target TD %", 0.25 to 2, step 0.25, default 1, "Add slicer to this page" ticked.
  3. Power BI makes the table, the column and the `… Value` measure.
- **Event markers:**
  1. Put `User fail %` and `Event marker (BD %)` both in **Y-axis**, and `Event text` and `Event source` in **Tooltips**.
  2. Format → Lines → pick the "Event marker" series → width 0.
  3. Format → Markers → on, size 8, orange.
- **Top N:** done with the `Avoidable top 5 (mn)` measure (see above). The filter-pane way works too: Filters → Bank → Filter type **Top N** → Show items Top 5 → By value `Avoidable at target (mn)`.
- **Gramin vs others line:**
  1. X-axis `year_label`, **Legend** `gramin_or_other` (a column made in `sql/02`: Gramin banks vs all other banks), Y-axis `System fail %`.
  2. Format → Lines → colors: Gramin red, others green.
  3. Data labels on.
  4. Analytics → Constant line 1 ("NPCI target 1%").
- **Constant (target) lines:** Analytics pane (magnifier icon) → Constant line → value 1 or 5 → label on.

## 4. Check numbers (must match SQL)

| Where | Expected |
|---|---|
| Page 1 cards (last 12 months) | 288.0 bn · 0.28% (2022: 1.45%) · 9.62% (2022: 6.71%) · 89.5% (2022: 77.3%) |
| Page 1 share chart | 18.6, 17.7, 16.4, 8.6, 4.9, 2.5 |
| Page 2 cards | −1.21 pts (total −1.05) · +0.52 pts (total +1.04) · +2.24 pts (total +2.32) |
| Page 2 payments moved | India Post + Airtel 1.9 → 6.7; Paytm 5.5 → 0 |
| Page 3 | Gramin 1.95% and 57.1%; line Gramin 3.66 … 1.93, others 1.52 … 0.23 |
| Page 4 at 1% | 63.4 mn (0.02%) · 75% (47.4 of 63.4) · 819.7 mn · ≈ ₹6,301 cr · top 5: 30.3, 9.8, 7.2, 5.3, 3.3 |

## 5. Interview answers you should be able to give
- **Why a measure and not a column?** A measure is recalculated for each filter (bank group, year, slider). You can't add up percentages, so % must be a measure.
- **Why `DIVIDE` and not `/`?** It gives blank instead of an error when the bottom number is 0.
- **What does `CALCULATE` do?** It runs a calculation with a changed filter, e.g. "only 2022" or "only the last 12 months".
- **What do `SUMX` and `RANKX` do?** `SUMX` works row by row, then adds up. `RANKX` ranks rows by a measure.
- **What does `TREATAS` do?** It lets two tables talk without a relationship, here the bank months and the event months.
- **Why no Year slicer on page 1?** The cards are fixed to the last 12 months to match the title. A Year slicer would make them disagree.
