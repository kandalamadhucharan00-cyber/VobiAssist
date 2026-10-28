from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Literal

DB_PATH = Path(__file__).resolve().parent.parent / "vobiassist.db"


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS call_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                call_id TEXT,
                source_number TEXT,
                destination_number TEXT,
                status TEXT,
                start_time TEXT,
                end_time TEXT,
                duration_seconds INTEGER,
                last_error TEXT,
                event_source TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                details TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS webhook_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT UNIQUE,
                event_type TEXT,
                source TEXT,
                status TEXT,
                payload TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS api_errors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service TEXT,
                status_code INTEGER,
                path TEXT,
                message TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        count = conn.execute("SELECT COUNT(*) FROM call_events").fetchone()[0]
        if count == 0:
            conn.execute(
                "INSERT INTO call_events (call_id, source_number, destination_number, status, start_time, end_time, duration_seconds, last_error, event_source, details) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    "call_1041",
                    "+14155550101",
                    "+14155550100",
                    "completed",
                    "2026-10-28T09:10:00Z",
                    "2026-10-28T09:12:00Z",
                    120,
                    None,
                    "Simulation",
                    json.dumps({"note": "Seeded demo session"}),
                ),
            )
            conn.execute(
                "INSERT INTO call_events (call_id, source_number, destination_number, status, start_time, end_time, duration_seconds, last_error, event_source, details) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    "call_1042",
                    "+14155550121",
                    "+14155550120",
                    "failed",
                    "2026-10-28T10:00:00Z",
                    "2026-10-28T10:01:30Z",
                    90,
                    "401 Unauthorized",
                    "Simulation",
                    json.dumps({"note": "Demo error"}),
                ),
            )
        error_count = conn.execute("SELECT COUNT(*) FROM api_errors").fetchone()[0]
        if error_count == 0:
            conn.execute(
                "INSERT INTO api_errors (service, status_code, path, message) VALUES (?, ?, ?, ?)",
                ("vobiz", 401, "/api/v1/Account/demo/Call/", "Authentication failed"),
            )


def add_call_event(
    *,
    call_id: str,
    source_number: str,
    destination_number: str,
    status: str,
    start_time: str | None = None,
    end_time: str | None = None,
    duration_seconds: int | None = None,
    last_error: str | None = None,
    event_source: Literal["Real Vobiz", "Simulation"] = "Simulation",
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO call_events (
                call_id, source_number, destination_number, status,
                start_time, end_time, duration_seconds, last_error,
                event_source, details
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                call_id,
                source_number,
                destination_number,
                status,
                start_time,
                end_time,
                duration_seconds,
                last_error,
                event_source,
                json.dumps(details or {}),
            ),
        )
        row_id = cursor.lastrowid
    return {"id": row_id, "call_id": call_id, "status": status}


def list_call_events(limit: int = 20, status: str | None = None, search: str | None = None) -> list[dict[str, Any]]:
    query = "SELECT * FROM call_events"
    clauses: list[str] = []
    params: list[str] = []
    if status:
        clauses.append("status = ?")
        params.append(status)
    if search:
        clauses.append("(call_id LIKE ? OR source_number LIKE ? OR destination_number LIKE ? OR last_error LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%"])
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(str(limit))
    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def get_call_event(call_id: str) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM call_events WHERE call_id = ? ORDER BY id DESC LIMIT 1", (call_id,)).fetchone()
    return dict(row) if row else None


def record_webhook_event(event_id: str, event_type: str, source: str, status: str, payload: dict[str, Any]) -> bool:
    with get_connection() as conn:
        try:
            conn.execute(
                "INSERT INTO webhook_events (event_id, event_type, source, status, payload) VALUES (?, ?, ?, ?, ?)",
                (event_id, event_type, source, status, json.dumps(payload)),
            )
            return True
        except sqlite3.IntegrityError:
            return False


def list_webhook_events(limit: int = 20) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM webhook_events ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    return [dict(row) for row in rows]


def add_api_error(service: str, status_code: int | None, path: str, message: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO api_errors (service, status_code, path, message) VALUES (?, ?, ?, ?)",
            (service, status_code, path, message),
        )


def get_api_errors(limit: int = 10) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM api_errors ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    return [dict(row) for row in rows]


def count_events() -> dict[str, int]:
    with get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM call_events").fetchone()[0]
        successful = conn.execute("SELECT COUNT(*) FROM call_events WHERE status = 'completed'").fetchone()[0]
        failed = conn.execute("SELECT COUNT(*) FROM call_events WHERE status = 'failed'").fetchone()[0]
    return {"total": total, "successful": successful, "failed": failed}
