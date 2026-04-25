"""Aggregate non-LinkedIn Milestone 1 sources (50% bucket — real APIs + optional file fallbacks)."""

from __future__ import annotations

from sources.civcast import fetch_civcast
from sources.constructconnect import fetch_constructconnect_leads
from sources.dodge import fetch_dodge
from sources.industry_database import fetch_industry_database
from sources.thomasnet import fetch_thomasnet


def fetch_non_linkedin_leads() -> list[dict]:
    records: list[dict] = []
    records.extend(fetch_thomasnet())
    records.extend(fetch_constructconnect_leads())
    records.extend(fetch_dodge())
    records.extend(fetch_civcast())
    records.extend(fetch_industry_database())
    return records
