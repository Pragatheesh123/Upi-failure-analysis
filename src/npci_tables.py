"""Parse NPCI UPI ecosystem-statistics pages into tidy tables.

NPCI publishes one block of tables per month:
  - "UPI Remitter Banks - Top 50 Banks (December'21)"   (renamed "Remitter Members" by Oct'24)
  - "UPI Beneficiary Banks - Top 50 Banks (December'21)"
  - "UPI Apps (Dec'21)"
  - "UPI P2P and P2M Transactions"

This module only knows how to read the HTML. It never invents values:
anything it cannot parse is reported, not filled in.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

import pandas as pd
from bs4 import BeautifulSoup

MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], start=1)}

# "(December'21)", "(Oct'24)", "(Sep 24)", "(December-2021)", "(Oct-2024)"
MONTH_RE = re.compile(r"\(\s*([A-Za-z]{3,9})[\s'’-]*(\d{2}|\d{4})\s*\)")


@dataclass
class RawTable:
    title: str
    kind: str                 # remitter | beneficiary | apps | p2p_p2m | other
    month: str | None         # "YYYY-MM"
    header: list[str]
    rows: list[list[str]] = field(default_factory=list)


def parse_month(text: str) -> str | None:
    m = MONTH_RE.search(text or "")
    if not m:
        return None
    mon = MONTHS.get(m.group(1)[:3].lower())
    if mon is None:
        return None
    yr = int(m.group(2))
    yr = yr + 2000 if yr < 100 else yr
    return f"{yr:04d}-{mon:02d}"


def classify(title: str) -> str:
    t = title.lower()
    if "remitter" in t and "ipo" not in t and "autopay" not in t:
        return "remitter"
    if "beneficiary" in t:
        return "beneficiary"
    if "upi apps" in t:
        return "apps"
    if "p2p" in t:
        return "p2p_p2m"
    return "other"


def _cells(tr) -> list[str]:
    return [c.get_text(" ", strip=True) for c in tr.find_all(["th", "td"])]


def parse_tables(html: str) -> list[RawTable]:
    """Return every <table> on the page with its title, kind, month and rows."""
    soup = BeautifulSoup(html, "lxml")
    out: list[RawTable] = []
    for table in soup.find_all("table"):
        trs = table.find_all("tr")
        if not trs:
            continue
        rows = [_cells(tr) for tr in trs]
        rows = [r for r in rows if any(c for c in r)]
        if not rows:
            continue

        # Title: first row that is a single non-empty cell, else the nearest heading/caption above.
        title = ""
        first_nonempty = [c for c in rows[0] if c]
        if len(first_nonempty) == 1 and not first_nonempty[0].replace(".", "").isdigit():
            title = first_nonempty[0]
            rows = rows[1:]
        if not title:
            cap = table.find("caption")
            prev = table.find_previous(["h1", "h2", "h3", "h4", "h5", "p", "strong"])
            title = (cap.get_text(" ", strip=True) if cap else "") or (
                prev.get_text(" ", strip=True) if prev else "")

        # Header: first row mentioning a column we know.
        hdr_idx = next((i for i, r in enumerate(rows)
                        if any(k in " ".join(r) for k in ("TD", "Volume", "Approved"))), None)
        header = rows[hdr_idx] if hdr_idx is not None else []
        body = rows[hdr_idx + 1:] if hdr_idx is not None else rows

        month = parse_month(title) or parse_month(" ".join(header))
        out.append(RawTable(title=title, kind=classify(title + " " + " ".join(header)),
                            month=month, header=header, rows=body))
    return out


def _num(s: str) -> float | None:
    s = (s or "").replace(",", "").replace("%", "").strip()
    if s in ("", "-", "NA", "N/A"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


REMITTER_COLS = {
    "total_volume_mn": ("total volume",),
    "approved_pct": ("approved",),
    "bd_pct": ("bd",),
    "td_pct": ("td",),
    "debit_reversal_count_mn": ("debit reversal count",),
    "debit_reversal_success_pct": ("debit reversal success",),
}


def _find_col(header: list[str], keys: tuple[str, ...]) -> int | None:
    norm = [re.sub(r"\s+", " ", h.lower()) for h in header]
    for i, h in enumerate(norm):
        for k in keys:
            # match "bd %"/"bd%"/"td%" exactly-ish, others by substring
            if k in ("bd", "td"):
                if re.fullmatch(rf"{k}\s*%?", h):
                    return i
            elif k in h:
                return i
    return None


def remitter_frame(t: RawTable) -> pd.DataFrame:
    """Turn one remitter table into tidy rows. Unparseable cells become NaN, never guesses."""
    idx = {name: _find_col(t.header, keys) for name, keys in REMITTER_COLS.items()}
    bank_i = _find_col(t.header, ("remitter",))
    if bank_i is None:
        bank_i = 1
    recs = []
    for r in t.rows:
        if len(r) <= bank_i or not r[bank_i]:
            continue
        rec = {"month": t.month, "rank_in_source": _num(r[0]), "bank_raw": r[bank_i]}
        for name, i in idx.items():
            rec[name] = _num(r[i]) if i is not None and i < len(r) else None
        rec["source_title"] = t.title
        recs.append(rec)
    return pd.DataFrame(recs)
