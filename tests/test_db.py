import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

import db as dbm


def test_encrypt_roundtrip_and_dedup(tmp_path, monkeypatch):
    monkeypatch.setattr(dbm, "DATA_ENC", tmp_path / "data.enc")
    monkeypatch.setattr(dbm, "SALT_FILE", tmp_path / "salt.bin")
    monkeypatch.setattr(dbm, "APP_DIR", tmp_path)

    assert not dbm.has_master()
    dbm.create_master("geheim-wachtwoord-123")
    assert not dbm.connected()
    assert dbm.has_master()

    assert dbm.unlock("verkeerd") is False
    assert dbm.unlock("geheim-wachtwoord-123") is True

    rows = [{
        "date": "2025-01-02",
        "description": "Albert Heijn 2456",
        "contra": "NL90",
        "amount": -62.40,
        "account": "NL21",
        "category": "Boodschappen",
        "kind": "variabel",
    }]
    added = dbm.insert_transactions(rows, "test.csv")
    assert added == 1
    added2 = dbm.insert_transactions([dict(r) for r in rows], "test.csv")
    assert added2 == 0

    dbm.set_setting("eigenwoningforfait_2025", "812")
    assert dbm.get_setting("eigenwoningforfait_2025") == "812"

    dbm.save_loonstrook("2025-01", 3450.0, 482.0, 103.0, 205.0, "test.pdf")
    dbm.save_loonstrook("2025-01", 3500.0, 482.0, 103.0, 205.0, "test.pdf")
    rows_ls = dbm.q("SELECT brutoloon FROM loonstroken WHERE period='2025-01'")
    assert len(rows_ls) == 1
    assert rows_ls[0]["brutoloon"] == 3500.0

    dbm.lock_down()
    assert dbm.DATA_ENC.exists()
    assert dbm.unlock("geheim-wachtwoord-123")
    assert len(dbm.q("SELECT * FROM transactions")) == 1
    dbm.lock_down()
