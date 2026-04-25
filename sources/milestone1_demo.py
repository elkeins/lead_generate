"""Synthetic leads for Milestone 1 dry-runs when live APIs are unavailable."""

from __future__ import annotations

_LI_COMPANIES = (
    "Northwind Industrial HVAC",
    "Contoso Marine Systems",
    "Fabrikam OEM Components",
    "Adventure Works Ventilation",
    "Litware Process Air",
    "Wide World Fans",
    "Blue Yonder Dampers",
    "Tailspin Dust Control",
    "Woodgrove Facility Services",
    "Proseware Engineering",
)

_NON_SOURCES = (
    ("ThomasNet", "ThomasNet category: industrial blowers / HVAC components."),
    ("Dodge Construction Network", "Dodge project: new manufacturing plant — HVAC package."),
    ("CIVcast", "CIVcast notice: public infrastructure — mechanical systems bid."),
    ("Industry database", "Verified OEM in target vertical (industrial air systems)."),
)


def fetch_demo_linkedin_leads(n: int = 50) -> list[dict]:
    hiring_titles = (
        "Mechanical Engineer — HVAC",
        "Senior HVAC Engineer",
        "Facility Engineer",
        "Project Engineer — industrial ventilation",
        "Manufacturing Engineer — process air",
    )
    expansion_snips = (
        "New plant expansion and additional cleanroom capacity.",
        "Groundbreaking on 200,000 sq ft facility expansion.",
    )
    product_snips = (
        "New product line launch for industrial dehumidification.",
        "R&D hiring for next-generation blower platform.",
    )
    out: list[dict] = []
    for i in range(n):
        company = (
            f"{_LI_COMPANIES[i % len(_LI_COMPANIES)]} — HVAC industrial (demo #{i})"
        )
        mod = i % 5
        if mod == 0:
            title = hiring_titles[i % len(hiring_titles)]
            evidence = f"{title} — hiring for technical team."
        elif mod == 1:
            title = "Construction Project Manager"
            evidence = expansion_snips[i % len(expansion_snips)]
        elif mod == 2:
            title = "Director of Engineering"
            evidence = product_snips[i % len(product_snips)]
        else:
            title = hiring_titles[(i + 1) % len(hiring_titles)]
            evidence = "Engineering careers: multiple HVAC / mechanical roles."
        is_profile = i % 2 == 1
        out.append(
            {
                "company": company,
                "website": f"https://demo-{i % 40}.example.com",
                "post_url": f"https://www.linkedin.com/jobs/view/{100000 + i}" if not is_profile else f"https://www.linkedin.com/in/demo-profile-{i}",
                "source": "LinkedIn Profiles" if is_profile else "LinkedIn Job Postings",
                "signal_category": "",
                "signal_evidence": evidence,
                "person_name": "Jordan Lee" if is_profile else "",
                "job_title": "Director of Engineering" if is_profile else title,
            }
        )
    return out


def fetch_demo_non_linkedin_leads(n: int = 50) -> list[dict]:
    out: list[dict] = []
    for i in range(n):
        src, base_ev = _NON_SOURCES[i % len(_NON_SOURCES)]
        mod = i % 3
        if mod == 0:
            cat_hint = "facility_expansion"
            ev = f"{base_ev} Expansion / new capacity signal #{i + 1}."
        elif mod == 1:
            cat_hint = "new_product_development"
            ev = f"{base_ev} Product / platform development signal #{i + 1}."
        else:
            cat_hint = "engineering_hires"
            ev = f"{base_ev} Hiring mechanical / HVAC engineers #{i + 1}."
        out.append(
            {
                "company": f"Demo OEM Partner {i + 1:02d} — industrial HVAC",
                "website": f"https://partner-{i % 30}.demo-industry.test",
                "post_url": f"https://signals.demo/{src.lower().replace(' ', '-')}/{i + 1}",
                "source": src,
                "signal_category": cat_hint,
                "signal_evidence": ev,
                "person_name": "Sam Morgan" if i % 4 == 0 else "",
                "job_title": "VP Operations" if i % 4 == 0 else "",
            }
        )
    return out
