import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

import db as dbm
import ib as ibm


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


def _setup(tmp_path, monkeypatch):
    monkeypatch.setattr(dbm, "DATA_ENC", tmp_path / "data.enc")
    monkeypatch.setattr(dbm, "SALT_FILE", tmp_path / "salt.bin")
    monkeypatch.setattr(dbm, "APP_DIR", tmp_path)
    dbm.create_master("geheim-wachtwoord-123")
    assert dbm.unlock("geheim-wachtwoord-123") is True


def test_afletterd_toggle(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)

    dbm.insert_transactions([{
        "date": "2025-02-01", "description": "Huur", "contra": "NL90",
        "amount": -900.0, "account": "NL21", "category": "Woning / Huur", "kind": "vast",
    }, {
        "date": "2025-02-03", "description": "Salaris", "contra": "NL99",
        "amount": 3000.0, "account": "NL21", "category": "Inkomsten", "kind": "inkomsten",
    }], "test.sta")
    rows = dbm.q("SELECT id FROM transactions ORDER BY id")

    assert dbm.toggle_afletterd(rows[0]["id"]) is True
    assert dbm.q("SELECT afletterd FROM transactions WHERE id=?", (rows[0]["id"],))[0]["afletterd"] == 1
    assert dbm.toggle_afletterd(rows[0]["id"]) is False
    assert dbm.toggle_afletterd(9999) is False

    n = dbm.set_afletterd_all("2025", True)
    assert n == 2
    assert all(r["afletterd"] == 1 for r in dbm.q("SELECT afletterd FROM transactions"))

    dbm.lock_down()
    assert dbm.unlock("geheim-wachtwoord-123")
    assert all(r["afletterd"] == 1 for r in dbm.q("SELECT afletterd FROM transactions"))
    dbm.lock_down()


def test_potjes_crud_en_saldo(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)

    pid = dbm.potje_add("Vakantie", 1000.0)
    assert pid > 0
    assert dbm.potjes_list()[0]["saldo"] == 0

    dbm.potje_mutate(pid, 250.0, "maart")
    dbm.potje_mutate(pid, 150.0, "april")
    dbm.potje_mutate(pid, -100.0, "auto gehuurd")

    rows = dbm.potjes_list()
    assert len(rows) == 1
    assert abs(rows[0]["saldo"] - 300.0) < 0.001
    assert abs(dbm.potjes_total() - 300.0) < 0.001

    muts = dbm.potje_mutaties(pid)
    assert len(muts) == 3
    assert muts[0]["mut_date"] >= muts[-1]["mut_date"]

    dbm.potje_add("Reserve", 0.0)
    assert len(dbm.potjes_list()) == 2
    reserve_id = dbm.q("SELECT id FROM potjes WHERE naam='Reserve'")[0]["id"]
    dbm.potje_delete(reserve_id)
    assert len(dbm.potjes_list()) == 1
    assert len(dbm.potje_mutaties(pid)) == 3

    dbm.lock_down()
    assert dbm.unlock("geheim-wachtwoord-123")
    assert abs(dbm.potjes_total() - 300.0) < 0.001
    dbm.lock_down()


def test_ib_box3_telt_potjes_mee(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)

    pid = dbm.potje_add("Vakantie", 500.0)
    dbm.potje_mutate(pid, 300.0, "start")
    dbm.set_setting("beginsaldo_2025", "1000")

    result = ibm.compute_year("2025")
    box3 = dict(result["box3"])
    assert "Spaarpotjes (opzij gezet)" in box3
    assert abs(box3["Spaarpotjes (opzij gezet)"] - 300.0) < 0.001
    assert abs(result["box3_total"] - 1300.0) < 0.001
    dbm.lock_down()
