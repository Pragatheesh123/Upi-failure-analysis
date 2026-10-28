"""Week 0 data check: which months of bank-wise decline data can we actually get?

Run on your own laptop (NPCI blocks many cloud servers):

    python src/check_sample.py                       # fetch the NPCI archive page
    python src/check_sample.py --file page.html      # or a page you saved with Ctrl+S

It saves the raw page into data/raw/, then prints and writes docs/data_inventory.csv:
one line per table found (month, kind, rows, columns) plus a sanity check that
Approved % + BD % + TD % adds up to ~100 for every remitter row.
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from npci_tables import MONTH_RE, parse_tables, remitter_frame  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_URL = "https://www.npci.org.in/what-we-do/upi/upi-ecosystem-statistics/archives"
HEADERS = {"User-Agent": "Mozilla/5.0 (portfolio data project; contact via GitHub)"}


def load(args) -> list[tuple[str, str]]:
    pages = []
    if args.file:
        for f in args.file:
            pages.append((f, Path(f).read_text(encoding="utf-8", errors="replace")))
        return pages
    import requests
    for url in args.url:
        r = requests.get(url, headers=HEADERS, timeout=60)
        r.raise_for_status()
        stamp = dt.date.today().isoformat()
        name = url.rstrip("/").split("/")[-1] or "page"
        out = ROOT / "data" / "raw" / f"npci_{name}_{stamp}.html"
        out.write_text(r.text, encoding="utf-8")
        print(f"saved {out.relative_to(ROOT)} ({len(r.text):,} chars)")
        pages.append((url, r.text))
    return pages


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--url", nargs="*", default=[ARCHIVE_URL])
    p.add_argument("--file", nargs="*")
    args = p.parse_args()

    inventory, remitters = [], []
    for source, html in load(args):
        tables = parse_tables(html)
        if not tables:
            print(f"!! {source}: no <table> found. The page may load data with JavaScript —"
                  " open it in a browser, Ctrl+S 'Webpage, complete', and rerun with --file.")
        for t in tables:
            inventory.append({"source": source, "month": t.month, "kind": t.kind,
                              "rows": len(t.rows), "title": t.title,
                              "columns": " | ".join(t.header),
                              "layout": MONTH_RE.sub("(<month>)", " | ".join(t.header))})
            if t.kind == "remitter":
                remitters.append(remitter_frame(t))

    inv = pd.DataFrame(inventory)
    if inv.empty:
        return 1
    (ROOT / "docs").mkdir(exist_ok=True)
    inv.to_csv(ROOT / "docs" / "data_inventory.csv", index=False)

    rem = inv[inv.kind == "remitter"].sort_values("month")
    print(f"\nRemitter-bank tables found: {len(rem)}")
    if not rem.empty:
        print(f"  first month: {rem.month.min()}   last month: {rem.month.max()}")
        print(f"  banks per month: {sorted(int(n) for n in rem.rows.unique())}")
        all_months = pd.period_range(rem.month.min(), rem.month.max(), freq="M").astype(str)
        missing = sorted(set(all_months) - set(rem.month.dropna()))
        print(f"  missing months in that range: {missing or 'none'}")
        no_month = rem.month.isna().sum()
        if no_month:
            print(f"  !! {no_month} remitter tables had no readable month in the title")
        print("\nColumn layouts seen (format changes show up as more than one line):")
        for cols, grp in rem.groupby("layout"):
            print(f"  {grp.month.min()} → {grp.month.max()}: {cols}")

    if remitters:
        df = pd.concat(remitters, ignore_index=True)
        df["pct_sum"] = df[["approved_pct", "bd_pct", "td_pct"]].sum(axis=1, min_count=3)
        off = df[(df.pct_sum - 100).abs() > 0.5]
        print(f"\nRows where Approved+BD+TD is not ~100%: {len(off)} of {len(df)}")
        if len(off):
            print(off[["month", "bank_raw", "approved_pct", "bd_pct", "td_pct", "pct_sum"]]
                  .head(20).to_string(index=False))
        print(f"\nDistinct raw bank names: {df.bank_raw.nunique()} "
              f"(case-insensitive: {df.bank_raw.str.lower().str.strip(' .').nunique()})")
    print("\nWrote docs/data_inventory.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
