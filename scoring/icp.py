"""Basic ICP score (0–10) plus short rationale (Milestone 1)."""

from __future__ import annotations

from config import (
    ICP_WEIGHT_COMPANY_FIT,
    ICP_WEIGHT_INDUSTRY_FIT,
    ICP_WEIGHT_ROLE_RELEVANCE,
    ICP_WEIGHT_SIGNAL_STRENGTH,
    TARGET_INDUSTRIES,
)


def score_industry(record: dict) -> int:
    blob = " ".join(
        [
            record.get("company", ""),
            record.get("job_title", ""),
            record.get("signal_evidence", ""),
        ]
    ).lower()
    score = 0
    if any(x.lower() in blob for x in TARGET_INDUSTRIES):
        score += 6
    if any(
        w in blob
        for w in (
            "hvac",
            "mechanical",
            "ventilation",
            "industrial",
            "marine",
            "oem",
            "construction",
            "facility",
            "process air",
            "blower",
            "damper",
        )
    ):
        score += 4
    return min(10, score)


def score_signal(signal_category: str, signal_evidence: str) -> int:
    text = (signal_evidence or "").lower()
    cat = (signal_category or "").lower()
    if cat == "engineering_hires":
        return 8
    if "engineer" in text and (
        "hiring" in text or "careers" in text or "recruit" in text or "job" in text
    ):
        return 8
    if cat == "facility_expansion" or "expansion" in text or "new plant" in text:
        return 10
    if cat == "new_product_development" or "new product" in text or "r&d" in text:
        return 9
    return 4


def score_role(job_title: str, person_name: str) -> int:
    title = (job_title or "").lower()
    if "engineer" in title or "project manager" in title or "procurement" in title:
        return 9
    if person_name and any(
        x in title for x in ("director", "vp", "vice president", "head", "chief")
    ):
        return 8
    if person_name:
        return 6
    return 3


def score_company_fit(record: dict) -> int:
    if record.get("website") and record.get("post_url"):
        return 10
    if record.get("website") or record.get("post_url"):
        return 7
    return 3


def _signal_label(cat: str) -> str:
    return {
        "engineering_hires": "engineer hiring / recruitment",
        "facility_expansion": "facility or capacity expansion",
        "new_product_development": "new product or R&D motion",
    }.get(cat, "industrial buying signal")


def _job_relevance_text(record: dict, role_pts: int) -> str:
    title = (record.get("job_title") or "").strip()
    person = (record.get("person_name") or "").strip()
    if role_pts >= 2 and title:
        return (
            f"High — role '{title}' aligns with specifier, influencer, or economic buyer "
            "profiles for industrial HVAC / air-handling decisions."
        )
    if person and title:
        return f"Medium — named contact ({person}) with title context: {title}."
    if title:
        return f"Medium — vacancy or title '{title}' indicates technical buying centre involvement."
    if person:
        return f"Medium — named decision-oriented contact: {person}."
    return "Lower — company-level signal without a named technical role yet; still useful for outreach routing."


def _icp_rationale_text(
    record: dict,
    industry: int,
    signal: int,
    role: int,
    company_fit: int,
    total: float,
) -> str:
    cat = record.get("signal_category") or "unknown"
    src = record.get("source") or "unknown"
    parts = [
        f"ICP {total:.1f}/10 from averaged components: industry fit ({industry}/10), "
        f"signal strength ({signal}/10), role relevance ({role}/10), and company/context fit ({company_fit}/10).",
        f"Why it matters: {_signal_label(cat)} in the HVAC / industrial stack, "
        f"sourced via {src}, matches XYZ-style project and OEM buying paths.",
    ]
    if record.get("person_name"):
        parts.append(
            "Named contact improves confidence this is a reachable decision path "
            "(vs. anonymous job-only signals)."
        )
    return " ".join(parts)


def score_record(record: dict) -> dict:
    industry = score_industry(record)
    signal = score_signal(record.get("signal_category", ""), record.get("signal_evidence", ""))
    role = score_role(record.get("job_title", ""), record.get("person_name", ""))
    company_fit = score_company_fit(record)

    weighted_sum = (
        (industry * ICP_WEIGHT_INDUSTRY_FIT)
        + (signal * ICP_WEIGHT_SIGNAL_STRENGTH)
        + (role * ICP_WEIGHT_ROLE_RELEVANCE)
        + (company_fit * ICP_WEIGHT_COMPANY_FIT)
    )
    weight_total = (
        ICP_WEIGHT_INDUSTRY_FIT
        + ICP_WEIGHT_SIGNAL_STRENGTH
        + ICP_WEIGHT_ROLE_RELEVANCE
        + ICP_WEIGHT_COMPANY_FIT
    )
    total = weighted_sum / weight_total if weight_total > 0 else 0.0
    total = max(0.0, min(10.0, total))

    record["industry_fit"] = industry
    record["signal_strength"] = signal
    record["role_relevance"] = role
    record["company_fit"] = company_fit
    record["icp_score"] = round(total, 1)
    record["job_relevance"] = _job_relevance_text(record, role)
    record["icp_rationale"] = _icp_rationale_text(
        record, industry, signal, role, company_fit, total
    )
    return record
