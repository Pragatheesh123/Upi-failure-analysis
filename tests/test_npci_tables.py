from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from npci_tables import parse_month, parse_tables, remitter_frame  # noqa: E402

HTML = (Path(__file__).parent / "fixtures" / "two_formats.html").read_text()


def test_month_formats():
    assert parse_month("Top 50 Banks (December'21)") == "2021-12"
    assert parse_month("Top 50 Members (Oct'24)") == "2024-10"
    assert parse_month("UPI Remitter Members (Oct-2024)") == "2024-10"
    assert parse_month("no month here") is None


def test_both_layouts_parse():
    tables = parse_tables(HTML)
    kinds = [(t.kind, t.month) for t in tables]
    assert kinds == [("remitter", "2021-12"), ("beneficiary", "2021-12"), ("remitter", "2024-10")]


def test_remitter_values_match_source():
    rem = [t for t in parse_tables(HTML) if t.kind == "remitter"]
    old, new = remitter_frame(rem[0]), remitter_frame(rem[1])
    sbi = old.iloc[0]
    assert (sbi.bank_raw, sbi.total_volume_mn, sbi.td_pct) == ("State Bank Of India", 1296.56, 4.43)
    assert new.iloc[1].bank_raw == "HDFC BANK LTD."
    assert new.iloc[0].debit_reversal_success_pct == 97.03
    for df in (old, new):
        total = df.approved_pct + df.bd_pct + df.td_pct
        assert ((total - 100).abs() <= 0.02).all()
