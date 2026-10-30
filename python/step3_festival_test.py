# STEP 3: FESTIVAL MONTHS TEST (question 7)
# Question: are system failures (TD) lower in festival months (Oct-Nov) than in other months?
# Same numbers as sql/09_q7_festival_months.sql, then a Mann-Whitney test to check it is not just luck.
# Run: python python/step3_festival_test.py

import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import mannwhitneyu


# ---------- 1. System fail % for every month ----------
banks = pd.read_csv("data/clean/upi_bank_monthly.csv")
banks["system_failed_mn"] = banks["total_volume_mn"] * banks["td_pct"] / 100

# add up all 50 banks per month, then failed / total (volume-weighted, like the SQL)
months = banks.groupby("month")[["system_failed_mn", "total_volume_mn"]].sum().reset_index()
months["system_fail_pct"] = months["system_failed_mn"] / months["total_volume_mn"] * 100
months["year"] = months["month"].str[:4]
months["is_festival_month"] = months["month"].str[5:].isin(["10", "11"])

# 2026 has no Oct-Nov yet, so leave it out
months = months[months["year"] != "2026"]


# ---------- 2. Compare each month with its own year ----------
# Failures fell every year, so a 2025 month always looks better than a 2022 month.
# Fair way: how far is each month above or below its year's average?
# Negative = better than usual for that year.
months["year_average"] = months.groupby("year")["system_fail_pct"].transform("mean")
months["gap_from_year_average"] = months["system_fail_pct"] - months["year_average"]

festival_months = months[months["is_festival_month"]]
other_months = months[~months["is_festival_month"]]   # ~ means NOT
festival = festival_months["gap_from_year_average"]
other = other_months["gap_from_year_average"]


# ---------- 3. Mann-Whitney test ----------
# It puts all months in order from best to worst and checks if festival months sit lower than chance would give.
# p-value = chance of seeing a difference this big if festival months were really no different.
# Below 0.05 = we can say festival months really are different.
result = mannwhitneyu(festival, other, alternative="two-sided")

print("Months compared:", len(festival), "festival,", len(other), "other (Aug 2021 to Dec 2025)")
print("Festival months, median gap from year average:", round(festival.median(), 3), "points")
print("Other months,    median gap from year average:", round(other.median(), 3), "points")
print("Mann-Whitney p-value:", round(result.pvalue, 4))
if result.pvalue < 0.05:
    print("Result: festival months are really different (not just luck).")
else:
    print("Result: the difference could be luck. We can't say festival months are different.")


# ---------- 4. Chart for the README ----------
plt.figure(figsize=(10, 4))
plt.plot(months["month"], months["system_fail_pct"], color="#1F3A5F", linewidth=2, label="All months")
plt.scatter(festival_months["month"], festival_months["system_fail_pct"],
            color="#E07A1F", s=50, zorder=3, label="Festival months (Oct-Nov)")
plt.axhline(1, color="grey", linestyle="--", linewidth=1)
plt.text(len(months) - 1, 1.03, "NPCI target: 1%", color="grey", ha="right")   # ha="right": text ends at the last month
plt.title("UPI system failure % (TD) by month")
plt.ylabel("System failure %")
plt.xticks(months["month"][::6], rotation=45)
plt.legend()
plt.tight_layout()
plt.savefig("images/q7_festival_months.png", dpi=150)
print()
print("Chart saved: images/q7_festival_months.png")
