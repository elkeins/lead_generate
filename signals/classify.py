"""Map raw text to one of three purchase signals (Milestone 1)."""

from __future__ import annotations

_HIRING_TERMS = (
    "engineer",
    "engineering",
    "mechanical",
    "hvac",
    "hiring",
    "careers",
    "job opening",
    "join our team",
    "recruit",
    "talent",
    "position:",
    "requisition",
)

_EXPANSION_TERMS = (
    "expansion",
    "new facility",
    "new plant",
    "groundbreaking",
    "square foot",
    "sq ft",
    "capacity increase",
    "brownfield",
    "greenfield",
    "campus expansion",
    "building addition",
    "new construction",
    "facility project",
)

_PRODUCT_TERMS = (
    "new product",
    "product launch",
    "product line",
    "r&d",
    "research and development",
    "patent",
    "introduces",
    "unveiled",
    "series launch",
    "next generation",
    "innovation",
)


def _blob(record: dict) -> str:
    parts = [
        str(record.get("job_title", "")),
        str(record.get("signal_evidence", "")),
        str(record.get("company", "")),
    ]
    return " ".join(parts).lower()


def apply_signal_classification(record: dict) -> dict:
    """Set ``signal_category`` and refine ``signal_evidence`` from record text."""
    text = _blob(record)
    current = (record.get("signal_category") or "").strip()
    valid_categories = {
        "engineering_hires",
        "facility_expansion",
        "new_product_development",
    }

    # Keep source-provided signal when present (e.g., project feeds already labeled).
    if current in valid_categories:
        category = current
        reason = record.get("signal_evidence") or "Signal: source-classified."
    else:
        scores = {
            "engineering_hires": sum(1 for t in _HIRING_TERMS if t in text),
            "facility_expansion": sum(1 for t in _EXPANSION_TERMS if t in text),
            "new_product_development": sum(1 for t in _PRODUCT_TERMS if t in text),
        }
        best = max(scores, key=scores.get)

        if scores[best] > 0:
            category = best
            reason_map = {
                "engineering_hires": "Signal: engineer hiring / technical recruitment activity.",
                "facility_expansion": "Signal: facility or capacity expansion language.",
                "new_product_development": "Signal: new product, R&D, or launch language.",
            }
            reason = reason_map[best]
        else:
            category = "engineering_hires"
            reason = "Signal: default — technical buyer motion (HVAC / industrial)."

    ev = (record.get("signal_evidence") or "").strip()
    if ev and reason.lower() not in ev.lower():
        record["signal_evidence"] = f"{ev} — {reason}"
    else:
        record["signal_evidence"] = ev or reason

    record["signal_category"] = category
    return record
