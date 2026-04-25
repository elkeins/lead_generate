def normalize_record(record: dict) -> dict:
    return {
        "company": str(record.get("company", "") or "").strip(),
        "website": str(record.get("website", "") or "").strip(),
        "post_url": str(record.get("post_url", "") or "").strip(),
        "source": str(record.get("source", "") or "").strip(),
        "signal_category": str(record.get("signal_category", "") or "").strip(),
        "signal_evidence": str(record.get("signal_evidence", "") or "").strip(),
        "person_name": str(record.get("person_name", "") or "").strip(),
        "job_title": str(record.get("job_title", "") or "").strip(),
        "job_relevance": str(record.get("job_relevance", "") or "").strip(),
        "icp_rationale": str(record.get("icp_rationale", "") or "").strip(),
    }
