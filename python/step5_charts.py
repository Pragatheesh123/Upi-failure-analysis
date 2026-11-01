# STEP 5: CHARTS FOR THE README
# Reads powerbi/data/bank_details.csv (made by sql/11_powerbi_export.sql), so the failed counts come from SQL.
# Here we only add them up and draw.
# Run: python python/step5_charts.py

import pandas as pd
import matplotlib.pyplot as plt

banks = pd.read_csv("powerbi/data/bank_details.csv", dtype={"year": str})
navy = "#1F3A5F"
red = "#C0392B"


# ---------- Chart 1 (Q1): system failures fell, user failures rose ----------
years = banks.groupby("year")[["system_failed_mn", "user_failed_mn", "total_volume_mn"]].sum()
years["system_fail_pct"] = years["system_failed_mn"] / years["total_volume_mn"] * 100
years["user_fail_pct"] = years["user_failed_mn"] / years["total_volume_mn"] * 100

# two small charts side by side, because the two % are on very different scales (0-2 vs 0-11)
fig, (left, right) = plt.subplots(1, 2, figsize=(10, 4))
left.bar(years.index, years["system_fail_pct"], color=navy)
left.axhline(1, color="grey", linestyle="--", linewidth=1)
left.set_title("System failure % (TD): target below 1%")
right.bar(years.index, years["user_fail_pct"], color=red)
right.axhline(5, color="grey", linestyle="--", linewidth=1)
right.set_title("Decline % (BD): target below 5%")
for ax, column in [(left, "system_fail_pct"), (right, "user_fail_pct")]:
    for year, value in years[column].items():
        ax.text(year, value, f"{value:.2f}", ha="center", va="bottom")   # number on top of each bar
fig.suptitle("UPI failures, top 50 banks (2021 = Aug-Dec, 2026 = Jan-Sep)")
plt.tight_layout()
plt.savefig("images/q1_system_vs_user_failures.png", dpi=150)


# ---------- Chart 2 (Q4 + Q5): Gramin banks are hit twice ----------
last_12 = banks[banks["month"] >= "2025-10"].copy()
last_12["refunds_worked_mn"] = last_12["debit_reversal_count_mn"] * last_12["debit_reversal_success_pct"] / 100
groups = last_12.groupby("bank_group")[["system_failed_mn", "total_volume_mn", "refunds_worked_mn"]].sum()
# refund success only counts rows where NPCI gave a refund %
has_refund = last_12[last_12["debit_reversal_success_pct"].notna()]
groups["refunds_needed_mn"] = has_refund.groupby("bank_group")["debit_reversal_count_mn"].sum()
groups["system_fail_pct"] = groups["system_failed_mn"] / groups["total_volume_mn"] * 100
groups["refund_success_pct"] = groups["refunds_worked_mn"] / groups["refunds_needed_mn"] * 100
groups = groups.sort_values("system_fail_pct")

fig, (left, right) = plt.subplots(1, 2, figsize=(10, 4))
colours = [red if g == "Gramin" else navy for g in groups.index]
left.barh(groups.index, groups["system_fail_pct"], color=colours)
left.axvline(1, color="grey", linestyle="--", linewidth=1)
left.set_title("System failure %")
left.set_xlim(0, groups["system_fail_pct"].max() * 1.2)   # room for the number after the longest bar
right.barh(groups.index, groups["refund_success_pct"], color=colours)
right.set_title("Automatic refund % (money taken, then failed)", fontsize=10)
right.set_xlim(0, 110)
for ax, column in [(left, "system_fail_pct"), (right, "refund_success_pct")]:
    for group, value in groups[column].items():
        ax.text(value, group, f" {value:.2f}", va="center")
fig.suptitle("Bank groups, last 12 months (Oct 2025 - Sep 2026)")
plt.tight_layout()
plt.savefig("images/q4_q5_gramin_hit_twice.png", dpi=150)

print(years[["system_fail_pct", "user_fail_pct"]].round(2))
print(groups[["system_fail_pct", "refund_success_pct"]].round(2))
print("Saved images/q1_system_vs_user_failures.png and images/q4_q5_gramin_hit_twice.png")
