# STEP 1: GET THE RAW DATA
#
# Downloads NPCI's monthly UPI tables (Jan 2022 to last month) into data/raw/npci_api/.
# npci.org.in is a JavaScript app: the page has no tables, it asks
# /api/ecosystem-statistics/get-statistics for them. We call that same address. No login needed.
#
# Run from the project folder:
#   python src/step1_get_raw_data.py                     # Jan 2022 to last month
#   python src/step1_get_raw_data.py 2026-09 2026-09     # only these months
#
# Every answer is saved exactly as received: data/raw/npci_api/<table>/<YYYY-MM>_p<page>.json
# Every request is logged in data/raw/npci_api/manifest.csv (time, status, file, URL).
# Files already saved are skipped, so it can be rerun after NPCI's server goes down.
import csv
import datetime
import json
import os
import sys
import time

import pandas as pd
import requests

OUT_DIR = "data/raw/npci_api"
MANIFEST = "data/raw/npci_api/manifest.csv"

API_URL = "https://www.npci.org.in/api/ecosystem-statistics/get-statistics"
HEADERS = {"User-Agent": "Mozilla/5.0 (portfolio data project; contact via GitHub)"}

# (folder name, tab_name, type_name) as listed by /api/ecosystem-statistics-page?product_name=upi
TABLES = [
    ("remitter", "top50-member", "remitter"),           # questions 1, 2, 3
    ("member_vol_val", "top-50-mem-vol-val", None),     # question 4: value per bank
    ("p2p_p2m", "p2p-and-p2m-transactions", None),      # question 5
    ("apps", "upi-apps", None),                         # supporting chart
]
PAGE_SIZE = 10             # the same page size the website uses
SECONDS_BETWEEN_CALLS = 1  # polite: fast enough, without loading a struggling server
SECONDS_AFTER_ERROR = 60   # the statistics server goes up and down; wait and retry
MAX_RETRIES = 60           # give up on one request after about an hour
# 503 = server down, 500/502/504 = server overloaded or too slow: all temporary
TEMPORARY_ERRORS = (500, 502, 503, 504)


def last_full_month():
    first_of_this_month = datetime.date.today().replace(day=1)
    return (first_of_this_month - datetime.timedelta(days=1)).strftime("%Y-%m")


def build_params(tab_name, type_name, month, page):
    params = {
        "product_name": "UPI",
        "tab_name": tab_name,
        "year": month[:4],
        "month": pd.Timestamp(month).strftime("%b"),  # NPCI wants "Jan", "Feb", ...
        "page_no": page,
        "size": PAGE_SIZE,
    }
    if type_name:
        params["type_name"] = type_name
    return params


def log_request(url, status, saved_file):
    os.makedirs(OUT_DIR, exist_ok=True)
    is_new = not os.path.exists(MANIFEST)
    with open(MANIFEST, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if is_new:
            writer.writerow(["fetched_at", "http_status", "file", "url"])
        writer.writerow([datetime.datetime.now().isoformat(timespec="seconds"), status, saved_file, url])


def fetch(params):
    """GET one page, waiting through temporary errors and timeouts."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(API_URL, params=params, headers=HEADERS, timeout=60)
        except (requests.Timeout, requests.ConnectionError):
            print(f"    no answer (timeout), waiting {SECONDS_AFTER_ERROR}s, try {attempt}/{MAX_RETRIES}")
            time.sleep(SECONDS_AFTER_ERROR)
            continue
        time.sleep(SECONDS_BETWEEN_CALLS)
        if response.status_code not in TEMPORARY_ERRORS:
            return response
        log_request(response.url, response.status_code, "")
        print(f"    HTTP {response.status_code} (server busy or down), "
              f"waiting {SECONDS_AFTER_ERROR}s, try {attempt}/{MAX_RETRIES}")
        time.sleep(SECONDS_AFTER_ERROR)
    sys.exit("NPCI did not answer for about an hour. Rerun later; saved files are kept.")


def collect_month(folder, tab_name, type_name, month):
    page = 1
    while True:
        out_file = f"{OUT_DIR}/{folder}/{month}_p{page}.json"
        if os.path.exists(out_file):
            with open(out_file, encoding="utf-8") as f:
                body = json.load(f)
        else:
            response = fetch(build_params(tab_name, type_name, month, page))
            if response.status_code in (401, 403, 429):
                # Blocked or rate-limited: stop instead of trying to get around it
                sys.exit(f"NPCI refused the request (HTTP {response.status_code}). Stopping.")
            if response.status_code != 200:
                # Not saved as data, so a rerun asks for this page again
                log_request(response.url, response.status_code, "")
                print(f"  {folder} {month} p{page}: HTTP {response.status_code}, not saved, moving on")
                return
            os.makedirs(f"{OUT_DIR}/{folder}", exist_ok=True)
            with open(out_file, "w", encoding="utf-8") as f:
                f.write(response.text)
            log_request(response.url, response.status_code, out_file)
            body = response.json()

        # The site reads data.totalCount to know how many pages there are
        total = body["data"]["totalCount"]
        print(f"  {folder} {month} p{page}: total rows {total}")
        if page * PAGE_SIZE >= total:
            return
        page += 1


def main():
    # Optional: first and last month on the command line, e.g. 2026-09 2026-09
    start = sys.argv[1] if len(sys.argv) > 1 else "2022-01"
    end = sys.argv[2] if len(sys.argv) > 2 else last_full_month()
    months = pd.period_range(start, end, freq="M").strftime("%Y-%m")

    print(f"Collecting {len(months)} months ({start} to {end}) for {len(TABLES)} tables")
    for folder, tab_name, type_name in TABLES:
        print(f"\n{folder}")
        for month in months:
            collect_month(folder, tab_name, type_name, month)
    print(f"\nDone. Request log: {MANIFEST}")


main()
