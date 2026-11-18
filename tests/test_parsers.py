import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

import categorize
import import_bank
import import_loon
import ib

FIX = Path(__file__).parent / "fixtures"


def test_camt_parsing():
    rows, fmt = import_bank.parse_any("camt053.xml", (FIX / "camt053.xml").read_bytes())
    assert fmt == "CAMT.053 (XML)"
    assert len(rows) == 2
    alf = rows[0]
    assert alf["amount"] == -62.40
    assert alf["date"] == "2025-01-02"
    assert "Albert Heijn" in alf["description"]
    assert alf["kind"] == "variabel"
    sal = rows[1]
    assert sal["amount"] == 2410.00
    assert sal["kind"] == "inkomsten"


def test_mt940_parsing():
    rows, fmt = import_bank.parse_any("export.sta", (FIX / "mt940.sta").read_bytes())
    assert fmt == "MT940"
    assert len(rows) == 2
    row_in = [r for r in rows if r["amount"] > 0][0]
    assert row_in["amount"] == 2410.00
    assert "WERKGEVER" in row_in["description"].upper()
    row_out = [r for r in rows if r["amount"] < 0][0]
    assert row_out["amount"] == -62.40
    assert row_out["date"] == "2025-01-02"
    assert row_out["contra"] == "NL90ABNA9876543210"


def test_csv_parsing():
    rows, fmt = import_bank.parse_any("ing_export.csv", (FIX / "ing_export.csv").read_bytes())
    assert fmt == "CSV"
    assert len(rows) == 2
    pins = rows[0]
    assert pins["amount"] == -62.40
    assert "ALBERT HEIJN" in pins["description"]
    assert pins["kind"] == "variabel"
    sal = rows[1]
    assert sal["amount"] == 2410.00
    assert sal["kind"] == "inkomsten"


def test_categorisatie_vast_variabel():
    assert categorize.apply("Hypotheek Rabobank rente") == ("Woning / Hypotheek", "vast")
    assert categorize.apply("Eneco Energie stroom") == ("Energie & Water", "vast")
    assert categorize.apply("Jumbo Bavel")[0] == "Boodschappen"
    assert categorize.apply("Salaris december")[1] == "inkomsten"
    assert categorize.apply("Onbekende winkel XY")[1] == "variabel"


def test_loonstrook_text():
    text = """LOONSTROOK december 2025
Belastbaar loon 3450,00
Ingehouden loonheffing 482,00
Pensioenpremie 103,00
Vakantiegeld 205,00
"""
    fields = import_loon.parse_loonstrook_text(text, source="test.pdf")
    assert fields["period"] == "2025-12"
    assert fields["brutoloon"] == 3450.00
    assert fields["loonheffing"] == 482.00
    assert fields["pensioen"] == 103.00
    assert fields["vakantiegeld"] == 205.00


def test_ib_export_csv():
    result = {
        "year": "2025",
        "box1": [("Loon", 1000.0)],
        "box1_total": 1000.0,
        "box3": [("Banktegoeden", 5000.0)],
        "box3_total": 5000.0,
        "loonstroken_count": 2,
        "tx_count": 5,
    }
    csv_text = ib.export_csv(result)
    assert "BOX I" in csv_text
    assert "1000,00" in csv_text
    assert "BOX III" in csv_text
