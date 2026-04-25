"""Milestone 1 — signal tracking, multi-source leads, ICP, 1.xlsx export."""

from __future__ import annotations

from config import (
    LINKEDIN_LEAD_TARGET,
    MILESTONE1_DEMO_MODE,
    MIN_FACILITY_EXPANSION_COUNT,
    MIN_ICP_SCORE,
    MIN_NEW_PRODUCT_DEVELOPMENT_COUNT,
    NON_LINKEDIN_LEAD_TARGET,
    STRICT_FIFTY_FIFTY,
    TARGET_LEAD_COUNT,
)
from scoring.icp import score_record
from signals.classify import apply_signal_classification
from sources.linkedin_jobs import fetch_linkedin_jobs
from sources.linkedin_profiles import fetch_linkedin_profiles
from sources.milestone1_demo import fetch_demo_linkedin_leads, fetch_demo_non_linkedin_leads
from sources.non_linkedin import fetch_non_linkedin_leads
from storage.xlsx_output import save_to_xlsx
from utils.clean import normalize_record
from utils.dedupe import dedupe_records
from utils.identity import is_linkedin_source, record_identity_key


def _icp_val(r: dict) -> float:
    try:
        return float(r.get("icp_score", 0))
    except (TypeError, ValueError):
        return 0.0


def select_balanced_milestone1_pool(records: list[dict]) -> list[dict]:
    """Prefer ``LINKEDIN_LEAD_TARGET`` + ``NON_LINKEDIN_LEAD_TARGET``.

    If ``STRICT_FIFTY_FIFTY`` is true, do not pad with extra LinkedIn rows when
    the non-LinkedIn pool has fewer than ``NON_LINKEDIN_LEAD_TARGET`` qualified
    leads (keeps the 50% non-LinkedIn requirement honest).
    """
    li = [r for r in records if is_linkedin_source(r.get("source", ""))]
    nl = [r for r in records if not is_linkedin_source(r.get("source", ""))]
    li.sort(key=lambda r: (-_icp_val(r), r.get("company", "")))
    nl.sort(key=lambda r: (-_icp_val(r), r.get("company", "")))

    if STRICT_FIFTY_FIFTY:
        n_li = min(LINKEDIN_LEAD_TARGET, len(li))
        n_nl = min(NON_LINKEDIN_LEAD_TARGET, len(nl))
        out = li[:n_li] + nl[:n_nl]
        if n_nl < NON_LINKEDIN_LEAD_TARGET:
            print(
                f"Warning: only {n_nl} qualified non-LinkedIn leads (need "
                f"{NON_LINKEDIN_LEAD_TARGET} for full 50/50). Configure ThomasNet "
                "(Apify), ConstructConnect (Dodge API), CIVcast URL, and industry "
                "database URL — see .env.example."
            )
        if len(out) < TARGET_LEAD_COUNT:
            print(
                f"Warning: output will have {len(out)} rows (target {TARGET_LEAD_COUNT}) "
                "until non-LinkedIn APIs return more qualified leads."
            )
        return out[:TARGET_LEAD_COUNT]

    out = li[:LINKEDIN_LEAD_TARGET] + nl[:NON_LINKEDIN_LEAD_TARGET]
    seen = {record_identity_key(r) for r in out}

    tail_dup: set[tuple[str, ...]] = set()
    candidates: list[dict] = []
    for r in li[LINKEDIN_LEAD_TARGET:] + nl[NON_LINKEDIN_LEAD_TARGET:]:
        k = record_identity_key(r)
        if k in seen or k in tail_dup:
            continue
        tail_dup.add(k)
        candidates.append(r)

    candidates.sort(key=lambda r: -_icp_val(r))
    for r in candidates:
        if len(out) >= TARGET_LEAD_COUNT:
            break
        k = record_identity_key(r)
        if k in seen:
            continue
        seen.add(k)
        out.append(r)
    return out[:TARGET_LEAD_COUNT]


def _enforce_signal_minimums(
    selected: list[dict],
    pool: list[dict],
    mins: dict[str, int],
) -> list[dict]:
    out = list(selected)
    selected_keys = {record_identity_key(r) for r in out}
    selected_counts = {
        sig: sum(1 for r in out if r.get("signal_category") == sig) for sig in mins
    }

    for sig, required in mins.items():
        if selected_counts.get(sig, 0) >= required:
            continue
        candidates = [r for r in pool if r.get("signal_category") == sig]
        candidates.sort(key=lambda r: (-_icp_val(r), r.get("company", "")))
        for r in candidates:
            if selected_counts[sig] >= required:
                break
            k = record_identity_key(r)
            if k in selected_keys:
                continue
            selected_keys.add(k)
            out.append(r)
            selected_counts[sig] = selected_counts.get(sig, 0) + 1

    out.sort(key=lambda r: (-_icp_val(r), r.get("company", "")))
    trimmed = out[:TARGET_LEAD_COUNT]
    trimmed_counts = {
        sig: sum(1 for r in trimmed if r.get("signal_category") == sig) for sig in mins
    }
    for sig, required in mins.items():
        if trimmed_counts.get(sig, 0) < required:
            print(
                f"Warning: selected only {trimmed_counts.get(sig, 0)} rows for {sig} "
                f"(target {required}). Add more source data for this signal."
            )
    return trimmed


def run_milestone1() -> None:
    if MILESTONE1_DEMO_MODE:
        print("Milestone 1: DEMO mode — synthetic data (not live ThomasNet / Dodge APIs).")
        raw = fetch_demo_linkedin_leads(max(LINKEDIN_LEAD_TARGET, 70)) + fetch_demo_non_linkedin_leads(
            max(NON_LINKEDIN_LEAD_TARGET, 70)
        )
    else:
        print("Milestone 1: live collection.")
        raw = (
            fetch_linkedin_jobs()
            + fetch_linkedin_profiles()
            + fetch_non_linkedin_leads()
        )
        print(f"  Raw rows fetched: {len(raw)}")

    cleaned = [normalize_record(dict(r)) for r in raw]
    for r in cleaned:
        apply_signal_classification(r)
    scored = [score_record(r) for r in cleaned]
    unique_all = dedupe_records(scored)
    qualified = [r for r in unique_all if _icp_val(r) >= MIN_ICP_SCORE]
    balanced = select_balanced_milestone1_pool(qualified)
    balanced = _enforce_signal_minimums(
        balanced,
        unique_all,
        {
            "facility_expansion": MIN_FACILITY_EXPANSION_COUNT,
            "new_product_development": MIN_NEW_PRODUCT_DEVELOPMENT_COUNT,
        },
    )

    save_to_xlsx(balanced)

    li_n = sum(1 for r in balanced if is_linkedin_source(r.get("source", "")))
    print(
        f"Saved {len(balanced)} leads to 1.xlsx "
        f"(LinkedIn-side sources: {li_n}, other sources: {len(balanced) - li_n}). "
        f"Qualified ICP>={MIN_ICP_SCORE} unique: {len(qualified)}."
    )
