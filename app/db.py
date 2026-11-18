import os
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

APP_DIR = Path(os.environ.get("APPDATA") or Path.home() / ".local" / "share") / "RicksBoekhoudProgramma"
DATA_ENC = APP_DIR / "data.enc"
SALT_FILE = APP_DIR / "salt.bin"
DB_NAME = "boekhouding.sqlite3"

_conn: sqlite3.Connection | None = None
_key: bytes | None = None
_temp_path: Path | None = None


def has_master() -> bool:
    return DATA_ENC.exists() and SALT_FILE.exists()


def _derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=300_000)
    return base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))


def _new_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tx_date TEXT NOT NULL,
            description TEXT NOT NULL,
            contra_account TEXT DEFAULT '',
            amount REAL NOT NULL,
            account TEXT DEFAULT '',
            category TEXT DEFAULT 'Overig',
            kind TEXT DEFAULT 'variabel',
            source TEXT DEFAULT '',
            fingerprint TEXT UNIQUE
        );
        CREATE TABLE IF NOT EXISTS loonstroken (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            period TEXT NOT NULL,
            brutoloon REAL DEFAULT 0,
            loonheffing REAL DEFAULT 0,
            pensioen REAL DEFAULT 0,
            vakantiegeld REAL DEFAULT 0,
            source TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT);
        CREATE INDEX IF NOT EXISTS idx_tx_date ON transactions(tx_date);
        CREATE INDEX IF NOT EXISTS idx_tx_cat ON transactions(category);
        """
    )
    conn.commit()
    conn.close()


def create_master(password: str) -> None:
    global _key, _conn, _temp_path
    APP_DIR.mkdir(parents=True, exist_ok=True)
    salt = os.urandom(16)
    SALT_FILE.write_bytes(salt)
    _key = _derive_key(password, salt)
    _temp_path = APP_DIR / DB_NAME
    _new_db(_temp_path)
    _conn = sqlite3.connect(_temp_path)
    lock_down()


def unlock(password: str) -> bool:
    global _key, _conn, _temp_path
    salt = SALT_FILE.read_bytes()
    try:
        _key = _derive_key(password, salt)
        plain = Fernet(_key).decrypt(DATA_ENC.read_bytes())
    except (InvalidToken, ValueError):
        _key = None
        return False
    _temp_path = Path(tempfile.gettempdir()) / f"ricks_boekhoud_{os.getpid()}.sqlite3"
    _temp_path.write_bytes(plain)
    _conn = sqlite3.connect(_temp_path)
    _conn.row_factory = sqlite3.Row
    return True


def lock_down() -> None:
    global _conn, _temp_path, _key
    if _conn is not None:
        _conn.commit()
        _conn.close()
        _conn = None
    if _temp_path is None or _key is None:
        return
    token = Fernet(_key).encrypt(_temp_path.read_bytes())
    APP_DIR.mkdir(parents=True, exist_ok=True)
    tmp_enc = DATA_ENC.with_suffix(".enc.tmp")
    tmp_enc.write_bytes(token)
    os.replace(tmp_enc, DATA_ENC)
    try:
        _temp_path.unlink()
    except OSError:
        pass
    _temp_path = None
    _key = None


def connected() -> bool:
    return _conn is not None


def q(sql: str, params: tuple = ()) -> list[sqlite3.Row]:
    assert _conn is not None, "Database is niet geopend"
    return _conn.execute(sql, params).fetchall()


def execute(sql: str, params: tuple = ()) -> int:
    assert _conn is not None, "Database is niet geopend"
    cur = _conn.execute(sql, params)
    _conn.commit()
    return cur.rowcount


def get_setting(key: str, default: str = "") -> str:
    rows = q("SELECT value FROM settings WHERE key=?", (key,))
    return rows[0]["value"] if rows else default


def set_setting(key: str, value: str) -> None:
    execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value),
    )


def insert_transactions(rows: list[dict], source: str) -> int:
    import hashlib

    added = 0
    for r in rows:
        fp = hashlib.sha256(
            f"{r['date']}|{r['amount']}|{r['description']}|{r['contra']}|{source}".encode("utf-8")
        ).hexdigest()
        added += execute(
            "INSERT OR IGNORE INTO transactions "
            "(tx_date, description, contra_account, amount, account, category, kind, source, fingerprint) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (
                r["date"], r["description"], r["contra"], r["amount"],
                r.get("account", ""), r["category"], r["kind"], source, fp,
            ),
        )
    return added


def save_loonstrook(period: str, brutoloon: float, loonheffing: float,
                    pensioen: float, vakantiegeld: float, source: str) -> None:
    existing = q("SELECT id FROM loonstroken WHERE period=?", (period,))
    if existing:
        execute(
            "UPDATE loonstroken SET brutoloon=?, loonheffing=?, pensioen=?, vakantiegeld=?, source=? "
            "WHERE id=?",
            (brutoloon, loonheffing, pensioen, vakantiegeld, source, existing[0]["id"]),
        )
    else:
        execute(
            "INSERT INTO loonstroken (period, brutoloon, loonheffing, pensioen, vakantiegeld, source) "
            "VALUES (?,?,?,?,?,?)",
            (period, brutoloon, loonheffing, pensioen, vakantiegeld, source),
        )


def stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
