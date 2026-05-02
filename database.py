# database.py — SQLite Database Handler for MiCitaBot

import sqlite3
import json
import uuid
from datetime import datetime
from config import DB_PATH


class Database:
    def __init__(self):
        self.path = DB_PATH
        self._init_db()

    def _conn(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Create tables if they don't exist"""
        with self._conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id     INTEGER PRIMARY KEY,
                    first_name  TEXT,
                    last_name   TEXT,
                    username    TEXT,
                    status      TEXT DEFAULT 'new',
                    created_at  TEXT DEFAULT (datetime('now')),
                    updated_at  TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS bookings (
                    id          TEXT PRIMARY KEY,
                    user_id     INTEGER,
                    data        TEXT,
                    status      TEXT DEFAULT 'pending',
                    result      TEXT,
                    created_at  TEXT DEFAULT (datetime('now')),
                    updated_at  TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                );
            """)

    # ── Users ──────────────────────────────────────────────────────────────────

    def save_user(self, user_id: int, first_name: str, last_name: str, username: str):
        with self._conn() as conn:
            existing = conn.execute(
                "SELECT user_id FROM users WHERE user_id = ?", (user_id,)
            ).fetchone()
            if existing:
                conn.execute(
                    "UPDATE users SET first_name=?, last_name=?, username=?, updated_at=datetime('now') WHERE user_id=?",
                    (first_name, last_name, username, user_id)
                )
            else:
                conn.execute(
                    "INSERT INTO users (user_id, first_name, last_name, username) VALUES (?, ?, ?, ?)",
                    (user_id, first_name, last_name, username)
                )

    def get_user_status(self, user_id: int) -> str | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT status FROM users WHERE user_id = ?", (user_id,)
            ).fetchone()
            return row["status"] if row else None

    def set_user_status(self, user_id: int, status: str):
        with self._conn() as conn:
            conn.execute(
                "UPDATE users SET status=?, updated_at=datetime('now') WHERE user_id=?",
                (status, user_id)
            )

    def get_pending_users(self) -> list:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM users WHERE status='pending' ORDER BY created_at"
            ).fetchall()
            return [dict(r) for r in rows]

    def get_all_users(self) -> list:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM users ORDER BY created_at DESC"
            ).fetchall()
            return [dict(r) for r in rows]

    # ── Bookings ───────────────────────────────────────────────────────────────

    def save_booking(self, user_id: int, data: dict) -> str:
        booking_id = str(uuid.uuid4())[:8].upper()
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO bookings (id, user_id, data, status) VALUES (?, ?, ?, 'pending')",
                (booking_id, user_id, json.dumps(data, ensure_ascii=False))
            )
        return booking_id

    def update_booking_status(self, booking_id: str, status: str, result: str = ""):
        with self._conn() as conn:
            conn.execute(
                "UPDATE bookings SET status=?, result=?, updated_at=datetime('now') WHERE id=?",
                (status, result, booking_id)
            )

    def get_last_booking(self, user_id: int) -> dict | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM bookings WHERE user_id=? ORDER BY created_at DESC LIMIT 1",
                (user_id,)
            ).fetchone()
            if row:
                r = dict(row)
                r["data"] = json.loads(r["data"])
                return r
            return None

    def get_user_bookings(self, user_id: int) -> list:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM bookings WHERE user_id=? ORDER BY created_at DESC",
                (user_id,)
            ).fetchall()
            result = []
            for r in rows:
                d = dict(r)
                d["data"] = json.loads(d["data"])
                result.append(d)
            return result


# Global instance
db = Database()
