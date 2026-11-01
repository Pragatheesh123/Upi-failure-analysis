# Resume bullets and LinkedIn post

Every number here was recalculated from `data/clean/` through the SQL files on 1 Nov 2026, after the Gramin bank merger fix.

## Resume (project section)

**Where Does UPI Fail? Bank-wise UPI failure analysis** | Python, PostgreSQL, Excel, Power BI | https://github.com/Pragatheesh123/Upi-failure-analysis

- Built a pipeline in Python (pandas) that downloads and cleans 5 years of NPCI data on India's top 50 UPI banks (3,100 bank-months), with automatic checks that caught and fixed an NPCI publishing error (Aug 2022 refund rates missing decimal points) and a bank merger that NPCI's tables counted twice.
- Wrote SQL (PostgreSQL) to split each change in failure rates into "rates at the banks themselves" vs "payments moved between banks": system failures fell 81% (1.45% to 0.28%) because rates fell at the banks themselves, while half the 2022–25 rise in declines came from payments shifting to payments banks with high declines.
- Found that regional rural (Gramin) banks fail most and refund least: 1.95% system failures (4x the next group) and only 57% of automatic refunds working vs 85–92% elsewhere; an Excel what-if model shows 63.4 mn failed payments could have been avoided in 12 months at NPCI's 1% target, 3 in 4 of them at just 3 Gramin banks.
- Tested a public claim that festival months have fewer failures (Mann-Whitney, SciPy): lower in every year but not statistically significant (p = 0.067), so reported as "not proven"; built a 4-page Power BI dashboard (DAX, what-if slider) that tells the story What → Why → Where → Cost and action, with owners for each recommendation.

Short version (if space is tight): keep bullets 2 and 3.

## LinkedIn post

My UPI payments kept failing, so I spent 3 weeks digging into NPCI's own data on India's top 50 banks (Aug 2021 – Sep 2026).

What I found:

📉 System failures (bank or NPCI side) fell 81%, from 1.45% in 2022 to 0.28% in the last 12 months. Rates fell at the banks themselves; payments didn't just move to better banks.

📈 Declines (a wrong PIN, low balance, or a limit set by the bank) rose from 6.7% to 9.6%, nearly double NPCI's 5% target. They dropped suddenly in May 2025 at almost every bank, then climbed every month. Why? Still an open question.

🏦 Regional rural (Gramin) banks fail most and refund least: the most system failures (1.95%), and when money is taken but the payment fails, only 57% of automatic refunds work, against 85–92% at other banks.

💡 If every bank had met NPCI's 1% target in the last 12 months, 63.4 million failed payments could have been avoided. That's only 0.02% of all payments, but 3 in 4 of them sit at just 3 Gramin banks, whose customers are mostly rural.

🎉 "Festival months have fewer failures"? Lower every year, but not statistically proven (p = 0.067).

Built with Python, PostgreSQL, Excel and Power BI. Code, SQL and every decision: https://github.com/Pragatheesh123/Upi-failure-analysis

#DataAnalytics #UPI #SQL #PowerBI #Python #Fintech

## Before posting
- Replace https://github.com/Pragatheesh123/Upi-failure-analysis with https://github.com/Pragatheesh123/Upi-failure-analysis
- Add the 4 Power BI screenshots (`images/powerbi_1_what.png` … `powerbi_4_cost_and_action.png`) to the post.
- Open the NPCI and RBI originals for the events in `sql/05` (NPCI OC 149 is checked; the others are news sites quoting them).
