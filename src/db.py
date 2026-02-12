"""Database operations using SQLite."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

from src.config import DB_PATH


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    """Get a database connection, creating the DB if needed."""
    path = db_path or DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(db_path: Path | None = None) -> None:
    """Initialize the database schema."""
    conn = get_connection(db_path)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS frameworks (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            display_name TEXT NOT NULL,
            description TEXT,
            base_version TEXT DEFAULT '1.0',
            config JSON NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS companies (
            id TEXT PRIMARY KEY,
            ticker TEXT NOT NULL,
            name TEXT NOT NULL,
            exchange TEXT,
            sector_framework_id TEXT REFERENCES frameworks(id),
            profile JSON NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS reports (
            id TEXT PRIMARY KEY,
            company_id TEXT REFERENCES companies(id),
            framework_id TEXT REFERENCES frameworks(id),
            status TEXT DEFAULT 'draft',
            report_date DATE,
            reference_quarter TEXT,
            sections JSON NOT NULL,
            citations JSON NOT NULL,
            qa_results JSON,
            word_count INTEGER,
            output_paths JSON,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS citations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL UNIQUE,
            title TEXT,
            publication TEXT,
            category TEXT,
            date_published DATE,
            date_accessed DATE,
            metadata JSON,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS prompt_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            framework_id TEXT REFERENCES frameworks(id),
            section_id INTEGER NOT NULL,
            prompt_type TEXT DEFAULT 'full',
            template TEXT NOT NULL,
            variables JSON,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()


def generate_id() -> str:
    """Generate a unique ID."""
    return str(uuid.uuid4())[:8]


# ── Framework CRUD ──

def save_framework(framework: dict, db_path: Path | None = None) -> str:
    """Save a framework to the database. Returns the framework ID."""
    conn = get_connection(db_path)
    fid = framework.get("id") or framework.get("sector_id") or generate_id()
    now = datetime.now().isoformat()
    conn.execute(
        """INSERT OR REPLACE INTO frameworks
           (id, name, display_name, description, base_version, config, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            fid,
            framework.get("name", fid),
            framework.get("display_name", fid),
            framework.get("description", ""),
            framework.get("base_version", "1.0"),
            json.dumps(framework),
            now,
            now,
        ),
    )
    conn.commit()
    conn.close()
    return fid


def get_framework(framework_id: str, db_path: Path | None = None) -> dict | None:
    """Retrieve a framework by ID."""
    conn = get_connection(db_path)
    row = conn.execute("SELECT * FROM frameworks WHERE id = ?", (framework_id,)).fetchone()
    conn.close()
    if row:
        return {**dict(row), "config": json.loads(row["config"])}
    return None


def list_frameworks(db_path: Path | None = None) -> list[dict]:
    """List all frameworks."""
    conn = get_connection(db_path)
    rows = conn.execute(
        "SELECT id, name, display_name, description, created_at FROM frameworks ORDER BY name"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_framework(framework_id: str, db_path: Path | None = None) -> bool:
    """Delete a framework. Returns True if deleted."""
    conn = get_connection(db_path)
    cur = conn.execute("DELETE FROM frameworks WHERE id = ?", (framework_id,))
    conn.commit()
    conn.close()
    return cur.rowcount > 0


# ── Company CRUD ──

def save_company(company: dict, db_path: Path | None = None) -> str:
    """Save a company profile. Returns the company ID."""
    conn = get_connection(db_path)
    cid = company.get("id") or generate_id()
    meta = company.get("metadata", {})
    now = datetime.now().isoformat()
    conn.execute(
        """INSERT OR REPLACE INTO companies
           (id, ticker, name, exchange, sector_framework_id, profile, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            cid,
            meta.get("ticker", ""),
            meta.get("name", ""),
            meta.get("exchange", ""),
            meta.get("sector_framework", ""),
            json.dumps(company),
            now,
            now,
        ),
    )
    conn.commit()
    conn.close()
    return cid


def get_company(company_id: str, db_path: Path | None = None) -> dict | None:
    """Retrieve a company by ID."""
    conn = get_connection(db_path)
    row = conn.execute("SELECT * FROM companies WHERE id = ?", (company_id,)).fetchone()
    conn.close()
    if row:
        return {**dict(row), "profile": json.loads(row["profile"])}
    return None


def get_company_by_ticker(ticker: str, db_path: Path | None = None) -> dict | None:
    """Retrieve a company by ticker symbol."""
    conn = get_connection(db_path)
    row = conn.execute(
        "SELECT * FROM companies WHERE ticker = ? ORDER BY updated_at DESC LIMIT 1",
        (ticker.upper(),),
    ).fetchone()
    conn.close()
    if row:
        return {**dict(row), "profile": json.loads(row["profile"])}
    return None


# ── Report CRUD ──

def save_report(report: dict, db_path: Path | None = None) -> str:
    """Save a report. Returns the report ID."""
    conn = get_connection(db_path)
    rid = report.get("id") or generate_id()
    now = datetime.now().isoformat()
    conn.execute(
        """INSERT OR REPLACE INTO reports
           (id, company_id, framework_id, status, report_date, reference_quarter,
            sections, citations, qa_results, word_count, output_paths, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            rid,
            report.get("company_id", ""),
            report.get("framework_id", ""),
            report.get("status", "draft"),
            report.get("report_date", ""),
            report.get("reference_quarter", ""),
            json.dumps(report.get("sections", [])),
            json.dumps(report.get("citations", [])),
            json.dumps(report.get("qa_results")),
            report.get("word_count", 0),
            json.dumps(report.get("output_paths", {})),
            now,
            now,
        ),
    )
    conn.commit()
    conn.close()
    return rid


def get_report(report_id: str, db_path: Path | None = None) -> dict | None:
    """Retrieve a report by ID."""
    conn = get_connection(db_path)
    row = conn.execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()
    conn.close()
    if row:
        result = dict(row)
        for field in ("sections", "citations", "qa_results", "output_paths"):
            if result[field]:
                result[field] = json.loads(result[field])
        return result
    return None


def get_reports_for_company(ticker: str, db_path: Path | None = None) -> list[dict]:
    """Get all reports for a company ticker."""
    conn = get_connection(db_path)
    rows = conn.execute(
        """SELECT r.* FROM reports r
           JOIN companies c ON r.company_id = c.id
           WHERE c.ticker = ?
           ORDER BY r.updated_at DESC""",
        (ticker.upper(),),
    ).fetchall()
    conn.close()
    results = []
    for row in rows:
        result = dict(row)
        for field in ("sections", "citations", "qa_results", "output_paths"):
            if result[field]:
                result[field] = json.loads(result[field])
        results.append(result)
    return results
