import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

APIFY_TOKEN = os.getenv("APIFY_TOKEN")

# Milestone 1 — lead volume and ICP gate
TARGET_LEAD_COUNT = int(os.getenv("TARGET_LEAD_COUNT", "100"))
LINKEDIN_LEAD_TARGET = int(os.getenv("LINKEDIN_LEAD_TARGET", "50"))
NON_LINKEDIN_LEAD_TARGET = int(os.getenv("NON_LINKEDIN_LEAD_TARGET", "50"))
MIN_ICP_SCORE = int(os.getenv("MIN_ICP_SCORE", "5"))
MIN_FACILITY_EXPANSION_COUNT = int(os.getenv("MIN_FACILITY_EXPANSION_COUNT", "20"))
MIN_NEW_PRODUCT_DEVELOPMENT_COUNT = int(
    os.getenv("MIN_NEW_PRODUCT_DEVELOPMENT_COUNT", "20")
)

# When true, output is at most 50 LinkedIn + 50 non-LinkedIn (no padding LinkedIn if NL < 50)
STRICT_FIFTY_FIFTY = os.getenv("STRICT_FIFTY_FIFTY", "true").lower() in (
    "1",
    "true",
    "yes",
)

# Set to 1 to run with synthetic 50/50 data (does not use real ThomasNet / Dodge APIs)
MILESTONE1_DEMO_MODE = os.getenv("MILESTONE1_DEMO_MODE", "").lower() in (
    "1",
    "true",
    "yes",
)

# --- ThomasNet.com (Apify actor; no official ThomasNet REST key) ---
APIFY_THOMASNET_ACTOR = os.getenv(
    "APIFY_THOMASNET_ACTOR", "zen-studio/thomasnet-suppliers-scraper"
).strip()
APIFY_THOMASNET_QUERIES = os.getenv("APIFY_THOMASNET_QUERIES", "").strip()
APIFY_THOMASNET_MAX_PER_QUERY = int(os.getenv("APIFY_THOMASNET_MAX_PER_QUERY", "40"))
THOMASNET_SCRAPE_MODE = os.getenv("THOMASNET_SCRAPE_MODE", "all").strip()

# --- Dodge Construction Network / ConstructConnect IO API ---
CONSTRUCTCONNECT_API_KEY = os.getenv("CONSTRUCTCONNECT_API_KEY", "").strip()
CONSTRUCTCONNECT_API_URL = os.getenv("CONSTRUCTCONNECT_API_URL", "").strip()

# --- CIVcast (vendor-specific; set URL + headers your account provides) ---
CIVCAST_API_URL = os.getenv("CIVCAST_API_URL", "").strip()
CIVCAST_HTTP_HEADERS_JSON = os.getenv("CIVCAST_HTTP_HEADERS_JSON", "").strip()

# --- Industry database (CSV path and/or JSON URL your org exposes) ---
INDUSTRY_LEADS_CSV = os.getenv("INDUSTRY_LEADS_CSV", "").strip()
INDUSTRY_LEADS_JSON_URL = os.getenv("INDUSTRY_LEADS_JSON_URL", "").strip()

# Manual JSON exports (optional fallbacks when no API URL is available)
DODGE_LEADS_JSON = os.getenv("DODGE_LEADS_JSON", "").strip()
CIVCAST_LEADS_JSON = os.getenv("CIVCAST_LEADS_JSON", "").strip()

TARGET_JOB_TITLES = [
    "Mechanical Engineer",
    "HVAC Engineer",
    "Project Engineer",
    "Facility Engineer",
    "Product Development Engineer",
    "Plant Expansion Project Manager",
]

TARGET_INDUSTRIES = [
    "Industrial Manufacturing",
    "HVAC",
    "OEM",
    "Marine",
    "Construction",
]

# Weighted-average ICP: each component is 0..10, final score is 0..10 average.
ICP_WEIGHT_INDUSTRY_FIT = float(os.getenv("ICP_WEIGHT_INDUSTRY_FIT", "1.0"))
ICP_WEIGHT_SIGNAL_STRENGTH = float(os.getenv("ICP_WEIGHT_SIGNAL_STRENGTH", "2.0"))
ICP_WEIGHT_ROLE_RELEVANCE = float(os.getenv("ICP_WEIGHT_ROLE_RELEVANCE", "1.0"))
ICP_WEIGHT_COMPANY_FIT = float(os.getenv("ICP_WEIGHT_COMPANY_FIT", "1.0"))

# --- Milestone 2 — outreach sequences, Instantly / SMTP, metrics dashboard ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
INSTANTLY_API_KEY = os.getenv("INSTANTLY_API_KEY", "").strip()
INSTANTLY_API_BASE = os.getenv("INSTANTLY_API_BASE", "https://api.instantly.ai").strip().rstrip("/")
# Existing Instantly campaign UUID (create in UI; sequence steps use {{m2_stepN_*}} custom vars).
MILESTONE2_INSTANTLY_CAMPAIGN_ID = os.getenv("MILESTONE2_INSTANTLY_CAMPAIGN_ID", "").strip()
MILESTONE2_LEADS_XLSX = os.getenv("MILESTONE2_LEADS_XLSX", "").strip()
MILESTONE2_MAX_LEADS = int(os.getenv("MILESTONE2_MAX_LEADS", "100"))
MILESTONE2_MIN_LEADS = int(os.getenv("MILESTONE2_MIN_LEADS", "50"))
MILESTONE2_SEQUENCE_STEPS = int(os.getenv("MILESTONE2_SEQUENCE_STEPS", "3"))
# Comma-separated days after previous send (len should match steps - 1); e.g. 3,5 → step2 +3d, step3 +5d after prior.
MILESTONE2_FOLLOWUP_GAP_DAYS = os.getenv("MILESTONE2_FOLLOWUP_GAP_DAYS", "3,5").strip()
MILESTONE2_SEND = os.getenv("MILESTONE2_SEND", "").lower() in ("1", "true", "yes")
MILESTONE2_DEMO_MODE = os.getenv("MILESTONE2_DEMO_MODE", "").lower() in ("1", "true", "yes")
# Synthetic contact emails when column empty (non-deliverable host; for pipeline dry-runs only).
MILESTONE2_DEMO_EMAIL_HOST = os.getenv(
    "MILESTONE2_DEMO_EMAIL_HOST", "milestone2.demo.invalid"
).strip()
# Shown in copy + From display name; use dedicated outreach subdomain in production DNS.
OUTREACH_SUBDOMAIN = os.getenv("OUTREACH_SUBDOMAIN", "").strip()
OUTREACH_SENDER_NAME = os.getenv("OUTREACH_SENDER_NAME", "HVAC outreach").strip()
OUTREACH_FROM_EMAIL = os.getenv("OUTREACH_FROM_EMAIL", "").strip()
OUTREACH_SMTP_HOST = os.getenv("OUTREACH_SMTP_HOST", "").strip()
OUTREACH_SMTP_PORT = int(os.getenv("OUTREACH_SMTP_PORT", "587"))
OUTREACH_SMTP_USER = os.getenv("OUTREACH_SMTP_USER", "").strip()
OUTREACH_SMTP_PASSWORD = os.getenv("OUTREACH_SMTP_PASSWORD", "").strip()
_ROOT = Path(__file__).resolve().parent
MILESTONE2_DB_PATH = os.getenv(
    "MILESTONE2_DB_PATH",
    str(_ROOT / "outreach_data" / "milestone2.sqlite"),
).strip()
MILESTONE2_DRAFTS_DIR = os.getenv(
    "MILESTONE2_DRAFTS_DIR",
    str(_ROOT / "outreach_data" / "drafts"),
).strip()
MILESTONE2_DASHBOARD_BIND = os.getenv("MILESTONE2_DASHBOARD_BIND", "127.0.0.1").strip()
MILESTONE2_DASHBOARD_PORT = int(os.getenv("MILESTONE2_DASHBOARD_PORT", "8765"))
