from apify_client import ApifyClient

from config import APIFY_TOKEN, TARGET_JOB_TITLES

# Apify Store: https://apify.com/valig/linkedin-jobs-scraper
LINKEDIN_JOBS_ACTOR = "valig/linkedin-jobs-scraper"

_TITLE_SIGNAL_HINTS: tuple[tuple[str, str], ...] = (
    ("Facility Expansion Manager", "facility_expansion"),
    ("Plant Expansion Project Manager", "facility_expansion"),
    ("Product Development Engineer", "new_product_development"),
    ("R&D Engineer", "new_product_development"),
)

_TARGETED_SEARCH_LIMIT = 45


def _is_apify_billing_limit_error(message: str) -> bool:
    m = (message or "").lower()
    return (
        "payment-signature" in m
        or "monthly usage hard limit exceeded" in m
        or "usage hard limit exceeded" in m
        or "hard limit exceeded" in m
        or "insufficient credits" in m
        or "payment required" in m
        or "402" in m
    )


def _extract_job_poster_name(item: dict) -> str:
    """Best-effort contact name from LinkedIn job JSON (field names vary by actor)."""
    key_candidates = (
        "posterName",
        "jobPosterName",
        "postedByName",
        "hiringManagerName",
        "recruiterName",
        "recruiterFullName",
        "recruiter",
        "contactName",
        "authorName",
        "employerContactName",
    )
    for k in key_candidates:
        v = item.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    jp_raw = item.get("jobPoster")
    if isinstance(jp_raw, str) and jp_raw.strip():
        return jp_raw.strip()
    nested_keys = (
        "poster",
        "jobPoster",
        "hiringManager",
        "recruiter",
        "postedBy",
        "author",
        "employer",
    )
    for nk in nested_keys:
        sub = item.get(nk)
        if isinstance(sub, dict):
            name = sub.get("name") or sub.get("fullName")
            if isinstance(name, str) and name.strip():
                return name.strip()
            first = sub.get("firstName")
            last = sub.get("lastName")
            if isinstance(first, str) and first.strip():
                return f"{first.strip()} {last.strip()}".strip() if isinstance(last, str) else first.strip()
    return ""


def fetch_linkedin_jobs() -> list[dict]:
    if not APIFY_TOKEN:
        print("Warning: APIFY_TOKEN not set. Skipping LinkedIn Jobs.")
        return []

    client = ApifyClient(APIFY_TOKEN)

    # Run broad engineering searches + targeted expansion/product searches.
    title_signal_pairs: list[tuple[str, str, int]] = [
        (t, "", 20) for t in TARGET_JOB_TITLES
    ]
    title_signal_pairs.extend(
        (title, signal, _TARGETED_SEARCH_LIMIT) for title, signal in _TITLE_SIGNAL_HINTS
    )

    try:
        all_items: list[dict] = []
        seen: set[object] = set()
        for title, signal_hint, limit in title_signal_pairs:
            run_input = {
                "title": title,
                "location": "United States",
                "limit": limit,
            }
            run = client.actor(LINKEDIN_JOBS_ACTOR).call(run_input=run_input)
            for item in client.dataset(run["defaultDatasetId"]).iterate_items():
                jid = item.get("id") or item.get("url") or (
                    item.get("title"),
                    item.get("companyName"),
                )
                if jid in seen:
                    continue
                seen.add(jid)
                if signal_hint and not item.get("signal_category"):
                    item["signal_category"] = signal_hint
                all_items.append(item)
    except Exception as e:
        error_msg = str(e)
        if _is_apify_billing_limit_error(error_msg):
            print(
                "Warning: LinkedIn Jobs scraper billing/usage limit reached. "
                "Skipping LinkedIn Jobs."
            )
            return []
        raise

    results: list[dict] = []
    for item in all_items:
        desc = (
            item.get("description")
            or item.get("jobDescription")
            or item.get("descriptionText")
            or ""
        )
        title = item.get("title") or ""
        desc_snip = str(desc)[:800] if desc else ""
        evidence = title if not desc_snip else f"{title} | {desc_snip}"
        poster = _extract_job_poster_name(item)
        results.append(
            {
                "company": item.get("companyName") or "",
                "website": str(item.get("companyWebsite") or item.get("companyUrl") or "").strip(),
                "post_url": str(item.get("url") or item.get("jobUrl") or item.get("link") or "").strip(),
                "source": "LinkedIn Job Postings",
                "signal_category": str(item.get("signal_category") or "").strip(),
                "signal_evidence": evidence,
                "person_name": poster,
                "job_title": title,
            }
        )

    return results
