import json
import sqlite3
from typing import Dict, List, Optional, Any
from config import DB_PATH
import datetime as dt


class Storage:
    def __init__(self, path: str = DB_PATH):
        self.path = path
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._ensure()

    def _ensure(self):
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS signals (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              source TEXT,
              url TEXT UNIQUE,
              title TEXT,
              snippet TEXT,
              detected_company TEXT,
              detected_domain TEXT,
              created_at TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS enrichments (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              signal_url TEXT UNIQUE,
              domain TEXT,
              tech_hints TEXT,
              company_size_hint TEXT,
              hiring_roles TEXT,
              updated_at TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS scores (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              signal_url TEXT UNIQUE,
              score INTEGER,
              reasons TEXT,
              updated_at TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS outreach (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              signal_url TEXT,
              channel TEXT,
              message TEXT,
              status TEXT,
              created_at TEXT
            )
            """
        )
        self.conn.commit()

    # Basic upserts
    def upsert_signal(self, source: str, url: str, title: str, snippet: str,
                      detected_company: str = "", detected_domain: str = ""):
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT OR IGNORE INTO signals(source, url, title, snippet, detected_company, detected_domain, created_at)
            VALUES(?,?,?,?,?,?,?)
            """,
            (source, url, title, snippet, detected_company, detected_domain,
             dt.datetime.now(dt.timezone.utc).isoformat())
        )
        cur.execute(
            """
            UPDATE signals SET detected_company = COALESCE(NULLIF(?, ''), detected_company),
                               detected_domain = COALESCE(NULLIF(?, ''), detected_domain)
            WHERE url = ?
            """,
            (detected_company, detected_domain, url)
        )
        self.conn.commit()

    def upsert_enrichment(self, signal_url: str, domain: str, tech_hints: Dict[str, int],
                           company_size_hint: str = "unknown", hiring_roles: List[str] | None = None):
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT OR REPLACE INTO enrichments(signal_url, domain, tech_hints, company_size_hint, hiring_roles, updated_at)
            VALUES(?,?,?,?,?,?)
            """,
            (
                signal_url,
                domain,
                json.dumps(tech_hints or {}),
                company_size_hint,
                ", ".join(hiring_roles or []),
                dt.datetime.now(dt.timezone.utc).isoformat(),
            )
        )
        self.conn.commit()

    def upsert_score(self, signal_url: str, score: int, reasons: List[str]):
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT OR REPLACE INTO scores(signal_url, score, reasons, updated_at)
            VALUES(?,?,?,?)
            """,
            (signal_url, score, json.dumps(reasons), dt.datetime.now(dt.timezone.utc).isoformat())
        )
        self.conn.commit()

    def insert_outreach(self, signal_url: str, channel: str, message: str, status: str = "draft"):
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO outreach(signal_url, channel, message, status, created_at)
            VALUES(?,?,?,?,?)
            """,
            (signal_url, channel, message, status, dt.datetime.now(dt.timezone.utc).isoformat())
        )
        self.conn.commit()

    # Fetch methods
    def fetch_signals(self, limit: int = 50) -> List[Dict[str, Any]]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM signals ORDER BY id DESC LIMIT ?", (limit,))
        return [dict(r) for r in cur.fetchall()]

    def fetch_signal_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM signals WHERE url=?", (url,))
        r = cur.fetchone()
        return dict(r) if r else None

    def fetch_joined(self, min_score: int = 0) -> List[Dict[str, Any]]:
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT s.*, e.tech_hints, e.company_size_hint, e.hiring_roles, sc.score, sc.reasons
            FROM signals s
            LEFT JOIN enrichments e ON e.signal_url = s.url
            LEFT JOIN scores sc ON sc.signal_url = s.url
            WHERE sc.score IS NULL OR sc.score >= ?
            ORDER BY COALESCE(sc.score, 0) DESC, s.id DESC
            """,
            (min_score,)
        )
        return [dict(r) for r in cur.fetchall()]

    def close(self):
        self.conn.close()
