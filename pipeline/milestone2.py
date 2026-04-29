"""Milestone 2 — AI/template sequences, Instantly bulk push, SMTP step-1 option, metrics + drafts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from config import (
    INSTANTLY_API_KEY,
    MILESTONE2_DASHBOARD_BIND,
    MILESTONE2_DASHBOARD_PORT,
    MILESTONE2_DB_PATH,
    MILESTONE2_DEMO_EMAIL_HOST,
    MILESTONE2_DEMO_MODE,
    MILESTONE2_DRAFTS_DIR,
    MILESTONE2_INSTANTLY_CAMPAIGN_ID,
    MILESTONE2_LEADS_XLSX,
    MILESTONE2_MAX_LEADS,
    MILESTONE2_MIN_LEADS,
    MILESTONE2_SEND,
)
from outreach import campaign_store
from outreach.instantly import build_instantly_lead_row, bulk_add_leads
from outreach.personalize import generate_sequence
from storage.xlsx_output import load_leads_from_xlsx
from utils.identity import record_identity_key


def _ensure_demo_email(lead: dict, index: int) -> str:
    key = "|".join(record_identity_key(lead))
    h = hashlib.sha256(key.encode("utf-8")).hexdigest()[:12]
    return f"m2-{h}-{index:04d}@{MILESTONE2_DEMO_EMAIL_HOST}"


def _resolve_email(lead: dict, index: int) -> str:
    em = (lead.get("email") or "").strip()
    if em:
        return em
    if MILESTONE2_DEMO_MODE:
        return _ensure_demo_email(lead, index)
    return ""


def run_milestone2() -> None:
    xlsx_path = (
        Path(MILESTONE2_LEADS_XLSX)
        if MILESTONE2_LEADS_XLSX
        else Path(__file__).resolve().parent.parent / "1.xlsx"
    )
    if not xlsx_path.is_file():
        print(f"Milestone 2: no leads file at {xlsx_path}. Run milestone 1 first or set MILESTONE2_LEADS_XLSX.")
        return

    leads = load_leads_from_xlsx(xlsx_path)
    if not leads:
        print("Milestone 2: spreadsheet has no data rows.")
        return

    prepared: list[tuple[dict, str, tuple[str, ...]]] = []
    seen_email: set[str] = set()
    for i, lead in enumerate(leads):
        email = _resolve_email(lead, i)
        if not email:
            continue
        el = email.lower()
        if el in seen_email:
            continue
        seen_email.add(el)
        row = dict(lead)
        row["email"] = email
        prepared.append((row, email, record_identity_key(row)))

    if len(prepared) < MILESTONE2_MIN_LEADS and not MILESTONE2_DEMO_MODE:
        print(
            f"Milestone 2: only {len(prepared)} leads with an email column (need >= {MILESTONE2_MIN_LEADS} "
            f"for the test band). Enrich `email` in {xlsx_path.name} or set MILESTONE2_DEMO_MODE=1 "
            f"for synthetic addresses at {MILESTONE2_DEMO_EMAIL_HOST}."
        )

    prepared = prepared[: MILESTONE2_MAX_LEADS]
    run_id = campaign_store.new_run_id()
    campaign_store.init_db(MILESTONE2_DB_PATH)
    campaign_store.insert_run(MILESTONE2_DB_PATH, run_id, note=f"source={xlsx_path.name}")

    drafts_path = Path(MILESTONE2_DRAFTS_DIR)
    drafts_path.mkdir(parents=True, exist_ok=True)
    jsonl_path = drafts_path / f"{run_id}_drafts.jsonl"

    instantly_rows: list[dict] = []
    with jsonl_path.open("w", encoding="utf-8") as jf:
        for lead, email, lkey in prepared:
            steps = generate_sequence(lead)
            lead_id = campaign_store.insert_lead_with_steps(
                MILESTONE2_DB_PATH,
                run_id,
                "|".join(lkey),
                email,
                lead,
                steps,
            )
            instantly_rows.append(build_instantly_lead_row(email, lead, steps))
            jf.write(
                json.dumps(
                    {
                        "lead_key": "|".join(lkey),
                        "email": email,
                        "company": lead.get("company"),
                        "steps": steps,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

    print(f"Milestone 2: wrote {len(prepared)} draft sequences to {jsonl_path}")
    print("  Client approval: review JSONL / DB sequence_steps before setting MILESTONE2_SEND=1.")

    if not MILESTONE2_SEND:
        print(
            "Milestone 2: dry run (no Instantly push). Set MILESTONE2_SEND=1 and "
            "INSTANTLY_API_KEY + MILESTONE2_INSTANTLY_CAMPAIGN_ID to upload leads."
        )
        _print_tail(run_id)
        return

    if INSTANTLY_API_KEY and MILESTONE2_INSTANTLY_CAMPAIGN_ID:
        chunk = 100
        for offset in range(0, len(instantly_rows), chunk):
            batch = instantly_rows[offset : offset + chunk]
            try:
                summary = bulk_add_leads(MILESTONE2_INSTANTLY_CAMPAIGN_ID, batch)
                campaign_store.record_event(
                    MILESTONE2_DB_PATH,
                    "instantly_pushed",
                    {"offset": offset, "batch_size": len(batch), "response": summary},
                    run_id=run_id,
                )
                print(f"  Instantly bulk add offset {offset}: {summary}")
            except Exception as e:
                print(f"  Instantly API error at offset {offset}: {e}")
                campaign_store.record_event(
                    MILESTONE2_DB_PATH,
                    "instantly_push_failed",
                    {"offset": offset, "error": str(e)},
                    run_id=run_id,
                )
    elif INSTANTLY_API_KEY and not MILESTONE2_INSTANTLY_CAMPAIGN_ID:
        print("Milestone 2: set MILESTONE2_INSTANTLY_CAMPAIGN_ID to push leads to Instantly.")

    _print_tail(run_id)


def _print_tail(run_id: str) -> None:
    stats = campaign_store.aggregate_stats(MILESTONE2_DB_PATH, run_id)
    print(
        f"  Metrics snapshot (run {run_id[:8]}…): leads={stats['leads_total']}, "
        f"open_rate={stats['open_rate_pct']}, reply_rate={stats['reply_rate_pct']}, "
        f"bounce_rate={stats['bounce_rate_pct']}"
    )
    print(
        f"  Dashboard: python main.py milestone2-dashboard "
        f"(http://{MILESTONE2_DASHBOARD_BIND}:{MILESTONE2_DASHBOARD_PORT}/?run_id={run_id})"
    )
