import sqlite3, json, uuid
from datetime import datetime
from config import DB_PATH

class Database:
    def __init__(self):
        self._init_db()

    def _conn(self):
        conn = sqlite3.connect(self.path if hasattr(self,'path') else DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id     INTEGER PRIMARY KEY,
                    first_name  TEXT,
                    last_name   TEXT,
                    username    TEXT,
                    status      TEXT DEFAULT 'new',
                    credits     INTEGER DEFAULT 0,
                    created_at  TEXT DEFAULT (datetime('now')),
                    updated_at  TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS bookings (
                    id            TEXT PRIMARY KEY,
                    user_id       INTEGER,
                    data          TEXT,
                    status        TEXT DEFAULT 'queued',
                    result        TEXT,
                    attempts      INTEGER DEFAULT 0,
                    next_retry    TEXT,
                    date_from     TEXT,
                    date_to       TEXT,
                    pdf_path      TEXT,
                    created_at    TEXT DEFAULT (datetime('now')),
                    updated_at    TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS otp_sessions (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    booking_id  TEXT,
                    otp_code    TEXT,
                    status      TEXT DEFAULT 'pending',
                    created_at  TEXT DEFAULT (datetime('now'))
                );
            """)

    # ── Users ──────────────────────────────────────────────────────────────────
    def save_user(self, user_id, first_name, last_name, username):
        with self._conn() as conn:
            row = conn.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,)).fetchone()
            if row:
                conn.execute(
                    "UPDATE users SET first_name=?,last_name=?,username=?,updated_at=datetime('now') WHERE user_id=?",
                    (first_name, last_name, username, user_id))
            else:
                conn.execute(
                    "INSERT INTO users(user_id,first_name,last_name,username) VALUES(?,?,?,?)",
                    (user_id, first_name, last_name, username))

    def get_user_status(self, user_id):
        with self._conn() as conn:
            row = conn.execute("SELECT status FROM users WHERE user_id=?", (user_id,)).fetchone()
            return row["status"] if row else None

    def set_user_status(self, user_id, status):
        with self._conn() as conn:
            conn.execute(
                "UPDATE users SET status=?,updated_at=datetime('now') WHERE user_id=?",
                (status, user_id))

    def get_credits(self, user_id):
        with self._conn() as conn:
            row = conn.execute("SELECT credits FROM users WHERE user_id=?", (user_id,)).fetchone()
            return row["credits"] if row else 0

    def add_credits(self, user_id, amount):
        with self._conn() as conn:
            conn.execute(
                "UPDATE users SET credits=credits+?,updated_at=datetime('now') WHERE user_id=?",
                (amount, user_id))

    def deduct_credit(self, user_id):
        with self._conn() as conn:
            conn.execute(
                "UPDATE users SET credits=credits-1,updated_at=datetime('now') WHERE user_id=?",
                (user_id,))

    def get_pending_users(self):
        with self._conn() as conn:
            rows = conn.execute("SELECT * FROM users WHERE status='pending' ORDER BY created_at").fetchall()
            return [dict(r) for r in rows]

    def get_all_users(self):
        with self._conn() as conn:
            rows = conn.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
            return [dict(r) for r in rows]

    # ── Bookings ───────────────────────────────────────────────────────────────
    def save_booking(self, user_id, data, date_from="", date_to=""):
        bid = str(uuid.uuid4())[:8].upper()
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO bookings(id,user_id,data,status,date_from,date_to,next_retry) VALUES(?,?,?,'queued',?,?,datetime('now'))",
                (bid, user_id, json.dumps(data, ensure_ascii=False), date_from, date_to))
        return bid

    def update_booking(self, bid, status, result="", pdf_path=""):
        with self._conn() as conn:
            conn.execute(
                "UPDATE bookings SET status=?,result=?,pdf_path=?,updated_at=datetime('now') WHERE id=?",
                (status, result, pdf_path, bid))

    def increment_attempts(self, bid):
        with self._conn() as conn:
            conn.execute(
                "UPDATE bookings SET attempts=attempts+1,next_retry=datetime('now','+5 minutes'),updated_at=datetime('now') WHERE id=?",
                (bid,))

    def get_queued_bookings(self):
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM bookings WHERE status IN ('queued','retrying') AND next_retry <= datetime('now') ORDER BY created_at"
            ).fetchall()
            result = []
            for r in rows:
                d = dict(r)
                d["data"] = json.loads(d["data"])
                result.append(d)
            return result

    def get_last_booking(self, user_id):
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM bookings WHERE user_id=? ORDER BY created_at DESC LIMIT 1",
                (user_id,)).fetchone()
            if row:
                d = dict(row)
                d["data"] = json.loads(d["data"])
                return d
            return None

    def get_user_bookings(self, user_id):
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM bookings WHERE user_id=? ORDER BY created_at DESC LIMIT 5",
                (user_id,)).fetchall()
            result = []
            for r in rows:
                d = dict(r)
                d["data"] = json.loads(d["data"])
                result.append(d)
            return result

    # ── OTP ───────────────────────────────────────────────────────────────────
    def save_otp(self, booking_id, otp):
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO otp_sessions(booking_id,otp_code) VALUES(?,?)",
                (booking_id, otp))

    def get_pending_otp(self, booking_id):
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM otp_sessions WHERE booking_id=? AND status='pending' ORDER BY created_at DESC LIMIT 1",
                (booking_id,)).fetchone()
            return dict(row) if row else None

    def mark_otp_used(self, booking_id):
        with self._conn() as conn:
            conn.execute(
                "UPDATE otp_sessions SET status='used' WHERE booking_id=?",
                (booking_id,))

    # ── Aliases for bot.py compatibility ──────────────────────────
    def create_booking(self, user_id, data):
        return self.save_booking(user_id, data,
            date_from=data.get("date_from",""),
            date_to=data.get("date_to",""))

    def get_booking(self, bid):
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM bookings WHERE id=?", (bid,)).fetchone()
            if row:
                d = dict(row)
                try: d["data"] = json.loads(d["data"])
                except Exception: pass
                return d
            return None

    def update_booking_status(self, bid, status, result=None):
        result_str = json.dumps(result) if result else ""
        self.update_booking(bid, status, result=result_str)

db = Database()
