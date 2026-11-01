# Resume bullets and LinkedIn post

Every number here was recalculated from `data/clean/` through the SQL files on 1 Nov 2026.

## Resume (project section)

**Where Does UPI Fail? Bank-wise UPI failure analysis** | Python, PostgreSQL, Excel, Power BI | [GitHub link]

- Built a pipeline in Python (pandas) that downloads and cleans 5 years of NPCI data on India's top 50 UPI banks (3,100 bank-months), with automatic checks that caught and fixed an NPCI publishing error (Aug 2022 refund rates missing decimal points).
- Wrote SQL (PostgreSQL) to split the change in failure rates into "banks improved" vs "payments moved between banks": system failures fell from 1.45% to 0.26% because banks really improved, while half the 2022–25 rise in user failures came from payments shifting to high-failure payments banks.
- Found that regional rural (Gramin) banks are hit twice: 1.95% system failures (4x the next group) and only 57% of refunds succeeding vs 85–92% elsewhere; an Excel what-if model shows bringing all banks to NPCI's 1% target would have saved 63.6 mn failed payments in 12 months, 83% of them at Gramin banks.
- Tested a public claim that festival months have fewer failures (Mann-Whitney, SciPy): lower in every year but not statistically significant (p = 0.067), so reported as "not proven"; built a 2-page Power BI dashboard (DAX) with a bank scorecard against NPCI targets.

Short version (if space is tight): keep bullets 2 and 3.

## LinkedIn post

My UPI payments kept failing, so I spent 3 weeks digging into NPCI's own data on India's top 50 banks (Aug 2021 – Sep 2026).

What I found:

📉 System failures (bank or NPCI errors) fell from 1.45% to 0.26%. The banks really improved; payments didn't just move to better banks.

📈 User-side failures (wrong PIN, low balance, limits) rose from 6.7% to 10.1%, double NPCI's 5% target. They dropped suddenly in May 2025 at 48 of 50 banks, then climbed every month. Why? Still an open question.

🏦 Regional rural (Gramin) banks are hit twice: the most system failures (1.95%), and when money is taken but the payment fails, only 57% of refunds succeed, against 85–92% at other banks.

💡 If every bank had met NPCI's 1% target in the last 12 months, 63.6 million failed payments would have gone through, 83% of them at about 10 Gramin banks that carry only 1.5% of UPI payments.

🎉 "Festival months have fewer failures"? Lower every year, but not statistically proven (p = 0.067).

Built with Python, PostgreSQL, Excel and Power BI. Code, SQL and every decision: [GitHub link]

#DataAnalytics #UPI #SQL #PowerBI #Python #Fintech

## Before posting
- Replace [GitHub link] with https://github.com/Pragatheesh123/Upi-failure-analysis
- Add the Power BI screenshots and `images/q4_q5_gramin_hit_twice.png` to the post.
- Open the NPCI and RBI originals for the events in `sql/05` (the sources now are news sites quoting them).
