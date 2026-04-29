"""SQLite persistence for Milestone 2 leads, sequence steps, and engagement events."""

from __future__ import annotations

import json
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any


def _connect(db_path: str) -> sqlite3.Connection:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str) -> None:
    conn = _connect(db_path)
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY,
                created_at REAL NOT NULL,
                note TEXT
            );
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                lead_key TEXT NOT NULL,
                email TEXT NOT NULL,
                company TEXT,
                person_name TEXT,
                job_title TEXT,
                signal_evidence TEXT,
                source TEXT,
                icp_score TEXT,
                payload_json TEXT,
                FOREIGN KEY (run_id) REFERENCES runs(id)
            );
            CREATE INDEX IF NOT EXISTS idx_leads_run ON leads(run_id);
            CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email);
            CREATE TABLE IF NOT EXISTS sequence_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER NOT NULL,
                step_index INTEGER NOT NULL,
                subject TEXT NOT NULL,
                body TEXT NOT NULL,
                delay_after_prev_days INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (lead_id) REFERENCES leads(id)
            );
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER,
                run_id TEXT,
                event_type TEXT NOT NULL,
                payload_json TEXT,
                created_at REAL NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
            CREATE INDEX IF NOT EXISTS idx_events_run ON events(run_id);
            """
        )
        conn.commit()
    finally:
        conn.close()


def new_run_id() -> str:
    return str(uuid.uuid4())


def insert_run(db_path: str, run_id: str, note: str = "") -> None:
    init_db(db_path)
    conn = _connect(db_path)
    try:
        conn.execute(
            "INSERT INTO runs (id, created_at, note) VALUES (?, ?, ?)",
            (run_id, time.time(), note),
        )
        conn.commit()
    finally:
        conn.close()


def insert_lead_with_steps(
    db_path: str,
    run_id: str,
    lead_key: str,
    email: str,
    lead: dict[str, Any],
    steps: list[dict[str, Any]],
) -> int:
    """steps: {subject, body, delay_after_prev_days}. Returns lead row id."""
    init_db(db_path)
    conn = _connect(db_path)
    try:
        cur = conn.execute(
            """
            INSERT INTO leads (run_id, lead_key, email, company, person_name, job_title,
                signal_evidence, source, icp_score, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                lead_key,
                email,
                lead.get("company", ""),
                lead.get("person_name", ""),
                lead.get("job_title", ""),
                lead.get("signal_evidence", ""),
                lead.get("source", ""),
                str(lead.get("icp_score", "")),
                json.dumps(lead, default=str),
            ),
        )
        lead_id = int(cur.lastrowid)
        for i, st in enumerate(steps):
            conn.execute(
                """
                INSERT INTO sequence_steps (lead_id, step_index, subject, body, delay_after_prev_days)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    lead_id,
                    i,
                    st.get("subject", ""),
                    st.get("body", ""),
                    int(st.get("delay_after_prev_days", 0)),
                ),
            )
        conn.execute(
            "INSERT INTO events (lead_id, run_id, event_type, payload_json, created_at) VALUES (?, ?, ?, ?, ?)",
            (
                lead_id,
                run_id,
                "draft_ready",
                json.dumps({"step_count": len(steps)}),
                time.time(),
            ),
        )
        conn.commit()
        return lead_id
    finally:
        conn.close()


def record_event(
    db_path: str,
    event_type: str,
    payload: dict[str, Any],
    *,
    lead_id: int | None = None,
    run_id: str | None = None,
) -> None:
    init_db(db_path)
    conn = _connect(db_path)
    try:
        conn.execute(
            "INSERT INTO events (lead_id, run_id, event_type, payload_json, created_at) VALUES (?, ?, ?, ?, ?)",
            (lead_id, run_id, event_type, json.dumps(payload, default=str), time.time()),
        )
        conn.commit()
    finally:
        conn.close()


def resolve_lead_id_by_email(db_path: str, email: str) -> int | None:
    init_db(db_path)
    conn = _connect(db_path)
    try:
        row = conn.execute(
            "SELECT id FROM leads WHERE lower(email) = lower(?) ORDER BY id DESC LIMIT 1",
            (email.strip(),),
        ).fetchone()
        return int(row["id"]) if row else None
    finally:
        conn.close()


def aggregate_stats(db_path: str, run_id: str | None = None) -> dict[str, Any]:
    init_db(db_path)
    conn = _connect(db_path)
    try:
        if run_id:
            lead_total = conn.execute(
                "SELECT COUNT(*) AS c FROM leads WHERE run_id = ?", (run_id,)
            ).fetchone()["c"]
            ev_where = "run_id = ?"
            ev_arg: tuple[Any, ...] = (run_id,)
        else:
            lead_total = conn.execute("SELECT COUNT(*) AS c FROM leads").fetchone()["c"]
            ev_where = "1=1"
            ev_arg = ()

        def count_event(t: str) -> int:
            row = conn.execute(
                f"SELECT COUNT(*) AS c FROM events WHERE {ev_where} AND event_type = ?",
                (*ev_arg, t),
            ).fetchone()
            return int(row["c"])

        opens = count_event("open") + count_event("email_opened")
        replies = count_event("reply") + count_event("email_replied")
        bounces = count_event("bounce") + count_event("email_bounced")
        sent = count_event("instantly_pushed") + count_event("smtp_sent")
        drafts = count_event("draft_ready")

        def rate(num: int, den: int) -> float | None:
            if den <= 0:
                return None
            return round(100.0 * num / den, 2)

        sent_denom = sent
        return {
            "leads_total": int(lead_total),
            "drafts_recorded": int(drafts),
            "sent_or_pushed": int(sent),
            "opens": int(opens),
            "replies": int(replies),
            "bounces": int(bounces),
            "open_rate_pct": rate(opens, sent_denom),
            "reply_rate_pct": rate(replies, sent_denom),
            "bounce_rate_pct": rate(bounces, sent_denom),
            "run_id": run_id,
            "updated_at": time.time(),
        }
    finally:
        conn.close()
