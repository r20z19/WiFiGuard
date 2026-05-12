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
    status TEXT DEFAULT '已处理',
    cleared_at TEXT
);

CREATE TABLE IF NOT EXISTS devices_online (
    mac TEXT PRIMARY KEY,
    ip TEXT,
    ssid TEXT,
    signal INTEGER,
    status TEXT DEFAULT '正常',
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS whitelist (
    mac TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    added_at TEXT NOT NULL
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
"""


def get_db():
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    conn = get_db()
    conn.executescript(SCHEMA)
    conn.execute(
        "INSERT OR IGNORE INTO email_config (id) VALUES (1)"
    )
    _init_default_user(conn)
    conn.commit()
    conn.close()


def _init_default_user(conn):
    exists = conn.execute("SELECT id FROM users WHERE username = ?", ("admin",)).fetchone()
    if not exists:
        now = "datetime('now')"
        password_hash = hashlib.sha256("123123".encode("utf-8")).hexdigest()
        conn.execute(
            "INSERT INTO users (username, password_hash, is_first_login, created_at) VALUES (?, ?, 1, datetime('now'))",
            ("admin", password_hash),
        )
