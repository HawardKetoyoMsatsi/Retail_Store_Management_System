"""Database connection and table creation (SQLite, built into Python)."""
import sqlite3

from config import DB_PATH


def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    with db() as con:
        con.executescript(
            """
            CREATE TABLE IF NOT EXISTS purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                item TEXT NOT NULL,
                buy REAL NOT NULL,
                sell REAL NOT NULL,
                qty REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS daily (
                date TEXT PRIMARY KEY,
                cash REAL NOT NULL DEFAULT 0,
                pochi REAL NOT NULL DEFAULT 0,
                mpesa REAL NOT NULL DEFAULT 0,
                spent REAL NOT NULL DEFAULT 0,
                drawn REAL NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS stocktake (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                item TEXT NOT NULL,
                qty REAL NOT NULL,
                price REAL NOT NULL,
                value REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value REAL NOT NULL
            );
            INSERT OR IGNORE INTO settings(key, value) VALUES ('capital', 0);
            CREATE TABLE IF NOT EXISTS catalog (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE COLLATE NOCASE,
                buy REAL NOT NULL DEFAULT 0,
                sell REAL NOT NULL DEFAULT 0
            );
            -- items already bought before the list existed are added to it automatically
            INSERT INTO catalog(name, buy, sell)
                SELECT TRIM(p.item), p.buy, p.sell FROM purchases p
                WHERE p.id = (SELECT MAX(id) FROM purchases
                              WHERE LOWER(TRIM(item)) = LOWER(TRIM(p.item)))
                  AND NOT EXISTS (SELECT 1 FROM catalog WHERE name = TRIM(p.item));
            """
        )
