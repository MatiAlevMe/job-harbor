import sqlite3
import os
from datetime import datetime
from typing import Optional

from .model import Job

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "jobs.db")


def _ensure_dir():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)


def get_connection() -> sqlite3.Connection:
    _ensure_dir()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT,
            remote INTEGER DEFAULT 0,
            url TEXT UNIQUE NOT NULL,
            description TEXT,
            requirements TEXT,
            source TEXT,
            salary_range TEXT,
            posted_date TEXT,
            match_score REAL DEFAULT 0.0,
            match_reason TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT DEFAULT (datetime('now')),
            total_jobs INTEGER DEFAULT 0,
            matched_jobs INTEGER DEFAULT 0,
            llm_used INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


def save_job(job: Job) -> bool:
    conn = get_connection()
    try:
        conn.execute("""
            INSERT OR IGNORE INTO jobs
                (title, company, location, remote, url, description,
                 requirements, source, salary_range, posted_date,
                 match_score, match_reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job.title, job.company, job.location, int(job.remote),
            job.url, job.description,
            "\n".join(job.requirements) if job.requirements else "",
            job.source, job.salary_range, job.posted_date,
            job.match_score, job.match_reason,
        ))
        conn.commit()
        return conn.total_changes > 0
    finally:
        conn.close()


def update_job_score(url: str, score: float, reason: str = ""):
    conn = get_connection()
    try:
        conn.execute("""
            UPDATE jobs SET match_score = ?, match_reason = ?,
                            updated_at = datetime('now')
            WHERE url = ?
        """, (score, reason, url))
        conn.commit()
    finally:
        conn.close()


def get_matched_jobs(min_score: float = 0.0, limit: int = 50) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT * FROM jobs WHERE match_score >= ?
            ORDER BY match_score DESC LIMIT ?
        """, (min_score, limit)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_all_jobs(limit: int = 100) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT * FROM jobs ORDER BY updated_at DESC LIMIT ?
        """, (limit,)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def log_run(total: int, matched: int, llm_used: bool = False):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO runs (total_jobs, matched_jobs, llm_used) VALUES (?, ?, ?)",
            (total, matched, int(llm_used)),
        )
        conn.commit()
    finally:
        conn.close()


def get_history(limit: int = 10) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM runs ORDER BY timestamp DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def job_exists(url: str) -> bool:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT 1 FROM jobs WHERE url = ?", (url,)
        ).fetchone()
        return row is not None
    finally:
        conn.close()
