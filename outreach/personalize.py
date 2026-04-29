"""Per-lead multi-step subjects/bodies — OpenAI when configured, else deterministic templates."""

from __future__ import annotations

import json
import re
from typing import Any

from config import (
    MILESTONE2_FOLLOWUP_GAP_DAYS,
    MILESTONE2_SEQUENCE_STEPS,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    OUTREACH_SENDER_NAME,
    OUTREACH_SUBDOMAIN,
)
from utils.http_post_json import post_json


def _first_name(person_name: str) -> str:
    person_name = (person_name or "").strip()
    if not person_name:
        return "there"
    return person_name.split()[0]


def _gaps_for_steps(n_steps: int) -> list[int]:
    raw = [x.strip() for x in MILESTONE2_FOLLOWUP_GAP_DAYS.split(",") if x.strip()]
    gaps = [int(x) for x in raw if x.isdigit()]
    while len(gaps) < max(0, n_steps - 1):
        gaps.append(3)
    return gaps[: max(0, n_steps - 1)]


def _template_sequence(lead: dict[str, Any], n_steps: int) -> list[dict[str, Any]]:
    company = (lead.get("company") or "your team").strip()
    fn = _first_name(lead.get("person_name", ""))
    title = (lead.get("job_title") or "").strip()
    sig = (lead.get("signal_evidence") or "")[:220].strip()
    website = (lead.get("website") or "").strip()
    icp = str(lead.get("icp_score", "")).strip()
    sub_hint = f" ({OUTREACH_SUBDOMAIN})" if OUTREACH_SUBDOMAIN else ""

    gaps = _gaps_for_steps(n_steps)
    steps: list[dict[str, Any]] = []
    subjects = (
        f"{company} — HVAC / industrial air projects",
        f"Re: expansion & equipment load at {company}",
        f"Last note — {company} and next steps",
    )
    bodies = (
        (
            f"Hi {fn},\n\n"
            f"I noticed {sig or 'activity that lines up with industrial HVAC / mechanical scope'} "
            f"at {company}.\n"
            f"We support OEMs and plants on fans, dampers, and related air-handling decisions — "
            f"especially when capacity or new lines add load to your system.\n\n"
            f"{'Relevant role context: ' + title + '. ' if title else ''}"
            f"{'ICP fit score in our file: ' + icp + '/10. ' if icp else ''}"
            f"{'Site for reference: ' + website + '\n' if website else ''}"
            f"\nWorth a five-minute look?\n\n"
            f"{OUTREACH_SENDER_NAME}{sub_hint}\n"
        ),
        (
            f"Hi {fn},\n\n"
            f"Circling back on {company}. If you are juggling facility expansion or new product "
            f"lines, timing on ventilation / process-air equipment often slips until late — "
            f"happy to share how similar teams de-risk that.\n\n"
            f"Original signal we saw: {sig[:180]}{'…' if len(sig) > 180 else ''}\n\n"
            f"{OUTREACH_SENDER_NAME}\n"
        ),
        (
            f"Hi {fn},\n\n"
            f"Closing the loop — if this is not relevant, no worries. "
            f"If projects or equipment specs are moving at {company}, "
            f"I can send a one-pager on how we engage (no spammy cadence).\n\n"
            f"{OUTREACH_SENDER_NAME}\n"
        ),
    )
    for i in range(n_steps):
        delay = 0 if i == 0 else gaps[i - 1]
        steps.append(
            {
                "subject": subjects[i % len(subjects)],
                "body": bodies[i % len(bodies)],
                "delay_after_prev_days": delay,
            }
        )
    return steps


_JSON_FENCE = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```", re.I)


def _parse_json_object(text: str) -> dict[str, Any]:
    text = text.strip()
    m = _JSON_FENCE.search(text)
    if m:
        text = m.group(1).strip()
    return json.loads(text)


def generate_sequence(lead: dict[str, Any]) -> list[dict[str, Any]]:
    n = max(2, min(5, MILESTONE2_SEQUENCE_STEPS))
    if not OPENAI_API_KEY:
        return _template_sequence(lead, n)

    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You write concise B2B outreach for industrial HVAC / mechanical OEMs and plants. "
                    "Return ONLY valid JSON, no markdown. Top-level key: steps (array). "
                    "Each step object: subject (string), body (plain text, short paragraphs), "
                    "delay_after_prev_days (integer; 0 for the first step, then days after the previous send). "
                    "Reference company, signal_evidence, job_title, person_name, website, icp_score when present. "
                    "No false claims, no pricing guarantees, professional tone."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "required_step_count": n,
                        "lead": dict(lead),
                        "sender_name": OUTREACH_SENDER_NAME,
                        "outreach_subdomain": OUTREACH_SUBDOMAIN or None,
                    },
                    default=str,
                ),
            },
        ],
        "temperature": 0.6,
    }
    try:
        data = post_json(
            "https://api.openai.com/v1/chat/completions",
            {
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            payload,
            timeout=60.0,
        )
        content = data["choices"][0]["message"]["content"]
        parsed = _parse_json_object(content)
        raw_steps = parsed.get("steps") or parsed
        if not isinstance(raw_steps, list):
            raise ValueError("missing steps array")
        out: list[dict[str, Any]] = []
        for i, st in enumerate(raw_steps[:n]):
            if not isinstance(st, dict):
                continue
            out.append(
                {
                    "subject": str(st.get("subject", "")).strip(),
                    "body": str(st.get("body", "")).strip(),
                    "delay_after_prev_days": int(st.get("delay_after_prev_days", 0 if i == 0 else 3)),
                }
            )
        if len(out) != n:
            out = _template_sequence(lead, n)
        return out[:n]
    except (RuntimeError, KeyError, ValueError, json.JSONDecodeError):
        return _template_sequence(lead, n)
