"""Download NPCI's monthly UPI tables from the website's own data feed.

npci.org.in is a JavaScript app: the page itself has no tables, it asks
/api/ecosystem-statistics/get-statistics for them. We call the same address.
No login is needed. See docs/decisions.md (28 Oct 2026).

    python src/collect_npci_api.py                 # Jan 2022 -> last month
    python src/collect_npci_api.py --start 2026-09 --end 2026-09

Every response is saved unchanged in data/raw/npci_api/<table>/<YYYY-MM>_p<page>.json,
and one line per request goes into data/raw/npci_api/manifest.csv (URL, time, status).
Files already saved are skipped, so the script can be rerun after an outage.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "raw" / "npci_api"
MANIFEST = OUT_DIR / "manifest.csv"

API_URL = "https://www.npci.org.in/api/ecosystem-statistics/get-statistics"
HEADERS = {"User-Agent": "Mozilla/5.0 (portfolio data project; contact via GitHub)"}

# (folder name, tab_name, type_name) as listed by /api/ecosystem-statistics-page?product_name=upi
TABLES = [
    ("remitter", "top50-member", "remitter"),           # questions 1, 2, 3
    ("member_vol_val", "top-50-mem-vol-val", None),     # question 4: value per bank
    ("p2p_p2m", "p2p-and-p2m-transactions", None),      # question 5
    ("apps", "upi-apps", None),                         # supporting chart
]
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
PAGE_SIZE = 10             # the same page size the website uses
SECONDS_BETWEEN_CALLS = 1  # polite: fast enough, without loading a struggling server
SECONDS_AFTER_ERROR = 60   # the statistics server goes up and down; wait and retry
MAX_RETRIES = 60           # give up on one request after about an hour
# 503 = server down, 500/502/504 = server overloaded or too slow: all temporary
TEMPORARY_ERRORS = (500, 502, 503, 504)


def month_range(start: str, end: str) -> list[str]:
    months = []
    year, month = int(start[:4]), int(start[5:])
    while f"{year:04d}-{month:02d}" <= end:
        months.append(f"{year:04d}-{month:02d}")
        month += 1
        if month == 13:
            year, month = year + 1, 1
    return months


def last_full_month() -> str:
    first_of_this_month = dt.date.today().replace(day=1)
    return (first_of_this_month - dt.timedelta(days=1)).strftime("%Y-%m")


def build_params(tab_name: str, type_name: str | None, month: str, page: int) -> dict:
    params = {
        "product_name": "UPI",
        "tab_name": tab_name,
        "year": month[:4],
        "month": MONTH_NAMES[int(month[5:]) - 1],
        "page_no": page,
        "size": PAGE_SIZE,
    }
    if type_name:
        params["type_name"] = type_name
    return params


def log_request(url: str, status: int, saved_file: str) -> None:
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    is_new = not MANIFEST.exists()
    with MANIFEST.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if is_new:
            writer.writerow(["fetched_at", "http_status", "file", "url"])
        writer.writerow([dt.datetime.now().isoformat(timespec="seconds"), status, saved_file, url])


def fetch(params: dict) -> requests.Response:
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
    raise SystemExit("NPCI did not answer for about an hour. Rerun later; saved files are kept.")


def total_rows(body: dict) -> int | None:
    # The site reads data.totalCount to draw its page numbers
    data = body.get("data")
    if isinstance(data, dict) and isinstance(data.get("totalCount"), int):
        return data["totalCount"]
    return None


def collect_month(folder: str, tab_name: str, type_name: str | None, month: str) -> None:
    page = 1
    while True:
        out_file = OUT_DIR / folder / f"{month}_p{page}.json"
        if out_file.exists():
            body = json.loads(out_file.read_text(encoding="utf-8"))
        else:
            response = fetch(build_params(tab_name, type_name, month, page))
            if response.status_code in (401, 403, 429):
                # Blocked or rate-limited: stop instead of trying to get around it
                raise SystemExit(f"NPCI refused the request (HTTP {response.status_code}). Stopping.")
            if response.status_code != 200:
                # Not saved as data, so a rerun asks for this page again
                log_request(response.url, response.status_code, "")
                print(f"  {folder} {month} p{page}: HTTP {response.status_code}, not saved, moving on")
                return
            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.write_text(response.text, encoding="utf-8")
            log_request(response.url, response.status_code, str(out_file.relative_to(ROOT)))
            body = response.json()

        total = total_rows(body)
        print(f"  {folder} {month} p{page}: total rows {total}")
        if total is None or page * PAGE_SIZE >= total:
            return
        page += 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="2022-01", help="first month, YYYY-MM")
    parser.add_argument("--end", default=last_full_month(), help="last month, YYYY-MM")
    args = parser.parse_args()

    months = month_range(args.start, args.end)
    print(f"Collecting {len(months)} months ({args.start} to {args.end}) for {len(TABLES)} tables")
    for folder, tab_name, type_name in TABLES:
        print(f"\n{folder}")
        for month in months:
            collect_month(folder, tab_name, type_name, month)
    print(f"\nDone. Request log: {MANIFEST.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
