# STEP 1: GET THE RAW DATA
#
# Downloads NPCI's monthly UPI tables (Jan 2022 to last month) and saves them in data/raw/.
# npci.org.in is a JavaScript app: the page has no tables, it asks
# /api/ecosystem-statistics/get-statistics for them. We call that same address. No login needed.
#
# Run from the project folder:   python python/step1_get_raw_data.py
#
# What it saves:
#   data/raw/npci_api/<table>/<YYYY-MM>_p<page>.json   every answer exactly as NPCI sent it
#   data/raw/npci_api/manifest.csv                      one line per request (time, status, file, URL)
#   data/raw/npci_<table>.csv                           all pages of a table in one CSV, values as text
# Files already saved are not downloaded again, so it can simply be rerun if NPCI's server goes down.
import time

import pandas as pd
import requests

START_MONTH = "2022-01"
END_MONTH = str(pd.Period(pd.Timestamp.today(), "M") - 1)   # last full month

API_URL = "https://www.npci.org.in/api/ecosystem-statistics/get-statistics"
HEADERS = {"User-Agent": "Mozilla/5.0 (portfolio data project; contact via GitHub)"}
MANIFEST = "data/raw/npci_api/manifest.csv"

# (folder name, tab_name, type_name) as listed by /api/ecosystem-statistics-page?product_name=upi
TABLES = [
    ("remitter", "top50-member", "remitter"),        # questions 1, 2, 3
    ("member_vol_val", "top-50-mem-vol-val", ""),    # question 4: value per bank
    ("p2p_p2m", "p2p-and-p2m-transactions", ""),     # question 5
    ("apps", "upi-apps", ""),                        # supporting chart
]
PAGE_SIZE = 10        # the same page size the website uses
MAX_TRIES = 60        # NPCI's server goes up and down: try each page for about an hour

months = pd.period_range(START_MONTH, END_MONTH, freq="M").strftime("%Y-%m")
print(f"Months {START_MONTH} to {END_MONTH}")

for folder, tab_name, type_name in TABLES:
    rows = []   # every row of this table, for the combined CSV

    for month in months:
        page = 1
        last_page = 1
        while page <= last_page:
            out_file = f"data/raw/npci_api/{folder}/{month}_p{page}.json"

            # Already saved? Read it. Not saved yet? Download it.
            try:
                answer = pd.read_json(out_file, typ="series")
            except FileNotFoundError:
                params = {
                    "product_name": "UPI",
                    "tab_name": tab_name,
                    "year": month[:4],
                    "month": pd.Timestamp(month).strftime("%b"),   # NPCI wants "Jan", "Feb", ...
                    "page_no": page,
                    "size": PAGE_SIZE,
                }
                if type_name != "":
                    params["type_name"] = type_name

                # Ask up to MAX_TRIES times. 500/502/503/504 or no answer = server busy, wait a minute.
                status = "no answer"
                for attempt in range(MAX_TRIES):
                    try:
                        response = requests.get(API_URL, params=params, headers=HEADERS, timeout=60)
                        status = response.status_code
                    except requests.RequestException:
                        status = "no answer"
                    time.sleep(1)   # be polite: one request per second at most
                    if status not in [500, 502, 503, 504, "no answer"]:
                        break
                    print(f"  {folder} {month} p{page}: {status}, waiting 60s (try {attempt + 1})")
                    time.sleep(60)

                if status in [401, 403, 429]:
                    # Blocked or rate-limited: stop instead of trying to get around it
                    raise SystemExit(f"NPCI refused the request ({status}). Stopping.")
                if status != 200:
                    # Not saved, so a rerun asks for this page again
                    raise SystemExit(f"{folder} {month} p{page}: got {status}. Rerun later, saved files are kept.")

                with open(out_file, "w", encoding="utf-8") as f:
                    f.write(response.text)
                log = pd.DataFrame([{
                    "fetched_at": pd.Timestamp.now().strftime("%Y-%m-%dT%H:%M:%S"),
                    "http_status": status,
                    "file": out_file,
                    "url": response.url,
                }])
                log.to_csv(MANIFEST, mode="a", header=False, index=False)
                print(f"  {folder} {month} p{page}: downloaded")
                answer = pd.read_json(out_file, typ="series")

            # Keep this page's rows, and work out how many pages the month has
            for row in answer["data"]["results"]:
                row["file_month"] = month
                rows.append(row)
            total_rows = answer["data"]["totalCount"]
            last_page = (total_rows + PAGE_SIZE - 1) // PAGE_SIZE   # e.g. 50 rows -> 5 pages
            page = page + 1

    # One CSV per table so cleaning can just use pd.read_csv. Values stay as text, as NPCI sent them.
    pd.DataFrame(rows).to_csv(f"data/raw/npci_{folder}.csv", index=False)
    print(f"Saved data/raw/npci_{folder}.csv ({len(rows)} rows)")
