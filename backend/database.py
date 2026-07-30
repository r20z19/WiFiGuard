import hashlib
import os
import sqlite3

from config import DATABASE_PATH


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    is_first_login INTEGER DEFAULT 1,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS alerts_current (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    severity TEXT NOT NULL,
    source_mac TEXT,
    target_mac TEXT,
    timestamp TEXT NOT NULL,
    suggestion TEXT,
    status TEXT DEFAULT '未处理'
);

CREATE TABLE IF NOT EXISTS alerts_history (
    id INTEGER PRIMARY KEY,
    type TEXT NOT NULL,
    severity TEXT NOT NULL,
    source_mac TEXT,
    target_mac TEXT,
    timestamp TEXT NOT NULL,
    suggestion TEXT,
    status TEXT DEFAULT '已删除',
    cleared_at TEXT
);

CREATE TABLE IF NOT EXISTS devices_online (
    mac TEXT PRIMARY KEY,
    ip TEXT,
    ssid TEXT,
    signal INTEGER,
    status TEXT DEFAULT '正常',
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    vendor TEXT DEFAULT '',
    pairwise_cipher TEXT DEFAULT '',
    group_cipher TEXT DEFAULT '',
    akm TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS whitelist (
    mac TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    added_at TEXT NOT NULL,
    device_type TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS blacklist (
    mac TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    reason TEXT NOT NULL,
    added_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS email_config (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    smtp_host TEXT DEFAULT 'smtp.qq.com',
    smtp_port INTEGER DEFAULT 465,
    email TEXT DEFAULT '',
    authorization_code TEXT DEFAULT '',
    recipient_email TEXT DEFAULT '',
    enabled INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS email_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    time TEXT NOT NULL,
    alert_type TEXT NOT NULL,
    recipient TEXT NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS system_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    level TEXT NOT NULL DEFAULT 'INFO',
    category TEXT NOT NULL DEFAULT 'system',
    message TEXT NOT NULL,
    detail TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS ai_config (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    provider TEXT NOT NULL DEFAULT 'deepseek',
    api_key TEXT NOT NULL DEFAULT '',
    enabled INTEGER DEFAULT 0
);
"""


def get_db():
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


MIGRATIONS = [
    "ALTER TABLE devices_online ADD COLUMN vendor TEXT DEFAULT ''",
    "ALTER TABLE devices_online ADD COLUMN pairwise_cipher TEXT DEFAULT ''",
    "ALTER TABLE devices_online ADD COLUMN group_cipher TEXT DEFAULT ''",
    "ALTER TABLE devices_online ADD COLUMN akm TEXT DEFAULT ''",
]


def init_db():
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    conn = get_db()
    conn.executescript(SCHEMA)
    for sql in MIGRATIONS:
        try:
            conn.execute(sql)
        except sqlite3.OperationalError:
            pass
    conn.execute(
        "INSERT OR IGNORE INTO email_config (id) VALUES (1)"
    )
    conn.execute(
        "INSERT OR IGNORE INTO ai_config (id, provider) VALUES (1, 'deepseek')"
    )
    _init_default_user(conn)
    conn.commit()
    conn.close()


def _init_default_user(conn):
    from services.auth_service import _hash_password, _verify_password

    exists = conn.execute(
        "SELECT id, is_first_login FROM users WHERE username = ?", ("admin",)
    ).fetchone()
    if not exists:
        password_hash = _hash_password("admin")
        conn.execute(
            "INSERT INTO users (username, password_hash, is_first_login, created_at) VALUES (?, ?, 1, datetime('now'))",
            ("admin", password_hash),
        )
        print("[DB] Created default admin user with password 'admin'")
        # Verify the hash works
        assert _verify_password("admin", password_hash), "Default password hash verification failed!"
        print("[DB] Default password hash verified OK")
    elif exists["is_first_login"] == 1:
        # Update default password for existing first-login users
        password_hash = _hash_password("admin")
        conn.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (password_hash, exists["id"]),
        )
        print("[DB] Updated existing admin user password to 'admin'")
        assert _verify_password("admin", password_hash), "Updated password hash verification failed!"
        print("[DB] Updated password hash verified OK")
    else:
        print(f"[DB] Admin user exists but is_first_login={exists['is_first_login']}, not updating password")
