"""
Deal Flow Pipeline - LinkedIn Scraper (via Google Dorking)
Finds founders in Consumer AI, Consumer Tech, and HealthTech building in/for India.
Uses Google search (no LinkedIn API needed).
"""

import json
import re
from pathlib import Path

from config import (
    MAFIA_COMPANIES, PREMIER_INSTITUTIONS,
    GOOGLE_DORK_TEMPLATES,
    TOP_COMPANIES
)
from utils import web_search as google_search  # DDG-primary, Google fallback


# Matches linkedin.com/in/<slug> anywhere in a URL or snippet
_LI_URL_RE = re.compile(r'linkedin\.com/in/([\w\-]+)')


INDIA_CITIES = [
    "Bengaluru", "Mumbai", "Delhi", "Hyderabad", "Pune",
    "Chennai", "Gurugram", "Noida", "Ahmedabad", "Kolkata",
]

FOUNDER_TITLES = [
    "Founder", "Co-Founder", "CEO", "Co-founder & CEO",
    "Founder & CEO", "Founding", "Building",
]

YEARS = ["2023", "2024", "2025"]


def _collect(queries: list[str], source_tag: str) -> list[dict]:
    """Run queries, extract linkedin.com/in/ URLs from results, return raw hits.

    site:linkedin.com/in is stripped at runtime - LinkedIn de-indexes most
    profiles from search engines, and GitHub Actions IPs are also blocked by
    DDG for site: queries.  Appending 'linkedin' biases results toward profiles
    without triggering the block.  LinkedIn URLs are captured from both the
    result URL and the snippet text.
    """
    hits: list[dict] = []
    seen_urls: set[str] = set()

    for q in queries:
        # Strip the site: operator; append 'linkedin' to bias toward profiles
        safe_q = re.sub(r'\bsite:linkedin\.com/in\s*', '', q).strip()
        if 'linkedin' not in safe_q.lower():
            safe_q += ' linkedin'

        print(f"  {safe_q[:80]}...")
        for r in google_search(safe_q):
            url     = r.get("url", "")
            snippet = r.get("snippet", "")
            title   = r.get("title", "")

            # 1. Result URL is a LinkedIn profile
            if "linkedin.com/in/" in url:
                li_url = url.split("?")[0]
            else:
                # 2. LinkedIn profile URL embedded in the snippet or title
                m = _LI_URL_RE.search(snippet + " " + title)
                li_url = f"https://www.linkedin.com/in/{m.group(1)}" if m else None

            if li_url:
                norm = li_url.rstrip("/").lower()
                if norm not in seen_urls:
                    seen_urls.add(norm)
                    hits.append({
                        "linkedin_url": li_url,
                        "title":        title,
                        "snippet":      snippet,
                        "query_source": source_tag,
                    })
    return hits


# ── Consumer AI ──────────────────────────────────────────────────────────────

def search_consumer_ai() -> list[dict]:
    """Broad Consumer AI founder search - India in/for India."""
    queries = [
        # Core AI building signals
        'site:linkedin.com/in "founder" "AI" "India" "building" 2024',
        'site:linkedin.com/in "founder" "AI" "India" "building" 2025',
        'site:linkedin.com/in "co-founder" "AI" "India" "building" 2024',
        'site:linkedin.com/in "co-founder" "AI" "India" "building" 2025',
        'site:linkedin.com/in "CEO" "AI startup" "India" 2024',
        'site:linkedin.com/in "CEO" "AI startup" "India" 2025',

        # GenAI / LLM
        'site:linkedin.com/in "generative AI" "India" founder 2024',
        'site:linkedin.com/in "generative AI" "India" founder 2025',
        'site:linkedin.com/in "LLM" "India" "founder" OR "building" 2024',
        'site:linkedin.com/in "LLM" "India" "founder" OR "building" 2025',
        'site:linkedin.com/in "GenAI" "India" founder startup 2025',
        'site:linkedin.com/in "agentic AI" "India" founder 2025',
        'site:linkedin.com/in "AI agent" "India" founder startup 2024',
        'site:linkedin.com/in "AI agent" "India" founder startup 2025',

        # Voice / vernacular AI
        'site:linkedin.com/in "voice AI" "India" founder 2024',
        'site:linkedin.com/in "voice AI" "India" founder 2025',
        'site:linkedin.com/in "vernacular AI" "India" founder 2024',
        'site:linkedin.com/in "vernacular AI" "India" founder 2025',
        'site:linkedin.com/in "Indic language" AI founder India 2024',
        'site:linkedin.com/in "Indic language" AI founder India 2025',

        # Personalisation / recommendation
        'site:linkedin.com/in "personalisation" OR "personalization" "AI" "India" founder 2024',
        'site:linkedin.com/in "recommendation engine" "India" founder startup 2024',
        'site:linkedin.com/in "AI-powered" "consumer" "India" founder 2025',

        # Copilot / assistant
        'site:linkedin.com/in "copilot" "India" founder startup 2024',
        'site:linkedin.com/in "copilot" "India" founder startup 2025',
        'site:linkedin.com/in "AI assistant" "India" founder 2024',
        'site:linkedin.com/in "AI assistant" "India" founder 2025',

        # Stealth / pre-launch
        'site:linkedin.com/in "stealth" "AI" "India" founder 2024',
        'site:linkedin.com/in "stealth" "AI" "India" founder 2025',
        'site:linkedin.com/in "pre-launch" "AI" "India" founder 2025',

        # City-specific AI
        *[f'site:linkedin.com/in "AI" "founder" "{city}" startup 2024' for city in INDIA_CITIES[:5]],
        *[f'site:linkedin.com/in "AI" "founder" "{city}" startup 2025' for city in INDIA_CITIES[:5]],

        # "Building for India" intent
        'site:linkedin.com/in "building for India" "AI" founder 2024',
        'site:linkedin.com/in "building for India" "AI" founder 2025',
        'site:linkedin.com/in "built for India" "AI" startup 2024',
        'site:linkedin.com/in "built for India" "AI" startup 2025',
        'site:linkedin.com/in "India-first" "AI" founder 2024',
        'site:linkedin.com/in "India-first" "AI" founder 2025',

        # YC / Antler AI India
        'site:linkedin.com/in "YC" "AI" "India" founder 2024',
        'site:linkedin.com/in "YC" "AI" "India" founder 2025',
        'site:linkedin.com/in "Antler" "AI" "India" founder 2024',
        'site:linkedin.com/in "Antler" "AI" "India" founder 2025',

        # Agentic / multi-agent AI
        'site:linkedin.com/in "agentic AI" "India" founder 2024',
        'site:linkedin.com/in "agentic AI" "India" founder 2025',
        'site:linkedin.com/in "autonomous AI" "India" founder startup 2025',
        'site:linkedin.com/in "AI workflow" "India" founder startup 2025',
        'site:linkedin.com/in "multi-agent" "India" founder startup 2025',

        # Foundation model / fine-tuning India
        'site:linkedin.com/in "foundation model" "India" founder 2024',
        'site:linkedin.com/in "fine-tuning" "India" founder startup 2025',
        'site:linkedin.com/in "RAG" "India" founder startup 2025',

        # AI for Bharat / India-specific AI
        'site:linkedin.com/in "AI for Bharat" founder startup 2024',
        'site:linkedin.com/in "AI for Bharat" founder startup 2025',
        'site:linkedin.com/in "Bharat AI" founder startup 2025',
        'site:linkedin.com/in "Hindi AI" OR "Hinglish AI" founder startup 2025',
    ]
    return _collect(queries, "consumer_ai_linkedin")


# ── Consumer Tech ─────────────────────────────────────────────────────────────

def search_consumer_tech() -> list[dict]:
    """Consumer Tech founder search - India market focus."""
    queries = [
        # General consumer tech
        'site:linkedin.com/in "consumer tech" "India" founder 2024',
        'site:linkedin.com/in "consumer tech" "India" founder 2025',
        'site:linkedin.com/in "founder" "marketplace" "India" 2024',
        'site:linkedin.com/in "founder" "marketplace" "India" 2025',
        'site:linkedin.com/in "founder" "D2C" "India" 2024',
        'site:linkedin.com/in "founder" "D2C" "India" 2025',

        # Fintech
        'site:linkedin.com/in "fintech" "India" founder startup 2024',
        'site:linkedin.com/in "fintech" "India" founder startup 2025',
        'site:linkedin.com/in "neobank" "India" founder 2024',
        'site:linkedin.com/in "neobank" "India" founder 2025',
        'site:linkedin.com/in "payments" "India" founder startup 2024',
        'site:linkedin.com/in "wealth management" "India" founder 2025',
        'site:linkedin.com/in "lending" "India" founder startup 2024',

        # EdTech
        'site:linkedin.com/in "edtech" "India" founder 2024',
        'site:linkedin.com/in "edtech" "India" founder 2025',
        'site:linkedin.com/in "online learning" "India" founder startup 2024',
        'site:linkedin.com/in "upskilling" "India" founder startup 2025',
        'site:linkedin.com/in "skills" "India" founder startup 2025',

        # Social / creator
        'site:linkedin.com/in "creator economy" "India" founder 2024',
        'site:linkedin.com/in "creator economy" "India" founder 2025',
        'site:linkedin.com/in "social commerce" "India" founder 2024',
        'site:linkedin.com/in "social commerce" "India" founder 2025',
        'site:linkedin.com/in "short video" "India" founder startup 2024',

        # Gaming / entertainment
        'site:linkedin.com/in "gaming" "India" founder startup 2024',
        'site:linkedin.com/in "gaming" "India" founder startup 2025',
        'site:linkedin.com/in "real money gaming" "India" founder 2024',

        # Travel / mobility
        'site:linkedin.com/in "travel tech" "India" founder 2024',
        'site:linkedin.com/in "mobility" "India" founder startup 2024',
        'site:linkedin.com/in "EV" "India" founder startup 2024',

        # Food / logistics / delivery
        'site:linkedin.com/in "food tech" "India" founder startup 2024',
        'site:linkedin.com/in "quick commerce" "India" founder 2024',
        'site:linkedin.com/in "q-commerce" "India" founder 2025',
        'site:linkedin.com/in "logistics" "India" founder startup 2024',

        # Fashion / beauty / retail
        'site:linkedin.com/in "fashion" "D2C" "India" founder 2024',
        'site:linkedin.com/in "beauty" "D2C" "India" founder 2024',
        'site:linkedin.com/in "retail tech" "India" founder 2024',

        # "Building for India" intent
        'site:linkedin.com/in "building for India" consumer founder 2024',
        'site:linkedin.com/in "building for India" consumer founder 2025',
        'site:linkedin.com/in "built for Bharat" founder 2024',
        'site:linkedin.com/in "built for Bharat" founder 2025',
        'site:linkedin.com/in "India-first" consumer founder startup 2024',
        'site:linkedin.com/in "India-first" consumer founder startup 2025',
        'site:linkedin.com/in "Bharat" founder startup 2024',
        'site:linkedin.com/in "Bharat" founder startup 2025',
        'site:linkedin.com/in "next billion users" "India" founder 2024',
        'site:linkedin.com/in "tier 2" OR "tier 3" "India" founder startup 2024',

        # City-specific consumer
        *[f'site:linkedin.com/in "consumer" "founder" "{city}" startup 2024' for city in INDIA_CITIES[:6]],
        *[f'site:linkedin.com/in "consumer" "founder" "{city}" startup 2025' for city in INDIA_CITIES[:4]],

        # Accelerator-backed
        'site:linkedin.com/in "YC" "consumer" "India" founder 2024',
        'site:linkedin.com/in "Antler" "consumer" "India" founder 2024',
        'site:linkedin.com/in "SURGE" "consumer" "India" founder 2024',

        # Climate / sustainability tech
        'site:linkedin.com/in "climate tech" "India" founder startup 2024',
        'site:linkedin.com/in "climate tech" "India" founder startup 2025',
        'site:linkedin.com/in "cleantech" "India" founder startup 2024',
        'site:linkedin.com/in "sustainable" "India" founder startup 2025',
        'site:linkedin.com/in "EV charging" "India" founder startup 2024',
        'site:linkedin.com/in "solar" "India" founder startup 2025',

        # AgriTech / Rural
        'site:linkedin.com/in "agritech" "India" founder startup 2024',
        'site:linkedin.com/in "agritech" "India" founder startup 2025',
        'site:linkedin.com/in "farmer" "India" founder startup 2024',
        'site:linkedin.com/in "rural" "India" founder startup 2025',

        # PropTech / Real Estate
        'site:linkedin.com/in "proptech" "India" founder startup 2024',
        'site:linkedin.com/in "real estate tech" "India" founder 2024',
        'site:linkedin.com/in "co-living" "India" founder startup 2024',

        # Wealthtech / Insurtech
        'site:linkedin.com/in "wealthtech" "India" founder startup 2024',
        'site:linkedin.com/in "insurtech" "India" founder startup 2025',
        'site:linkedin.com/in "personal finance" "India" founder startup 2025',
    ]
    return _collect(queries, "consumer_tech_linkedin")


# ── HealthTech ────────────────────────────────────────────────────────────────

def search_healthtech() -> list[dict]:
    """HealthTech founder search - India patients, doctors, hospitals."""
    queries = [
        # General healthtech
        'site:linkedin.com/in "healthtech" "India" founder 2024',
        'site:linkedin.com/in "healthtech" "India" founder 2025',
        'site:linkedin.com/in "health tech" "India" founder startup 2024',
        'site:linkedin.com/in "health tech" "India" founder startup 2025',
        'site:linkedin.com/in "healthcare" "India" founder startup 2024',
        'site:linkedin.com/in "healthcare" "India" founder startup 2025',
        'site:linkedin.com/in "medtech" "India" founder 2024',
        'site:linkedin.com/in "medtech" "India" founder 2025',
        'site:linkedin.com/in "digital health" "India" founder 2024',
        'site:linkedin.com/in "digital health" "India" founder 2025',

        # Telemedicine / doctor
        'site:linkedin.com/in "telemedicine" "India" founder 2024',
        'site:linkedin.com/in "telemedicine" "India" founder 2025',
        'site:linkedin.com/in "doctor" "startup" "India" founder 2024',
        'site:linkedin.com/in "doctor-patient" "India" founder 2024',

        # Mental health
        'site:linkedin.com/in "mental health" "India" founder startup 2024',
        'site:linkedin.com/in "mental health" "India" founder startup 2025',
        'site:linkedin.com/in "therapy" "India" founder startup 2024',
        'site:linkedin.com/in "wellness" "India" founder startup 2024',
        'site:linkedin.com/in "wellness" "India" founder startup 2025',

        # Women's health / femtech
        'site:linkedin.com/in "femtech" "India" founder 2024',
        'site:linkedin.com/in "femtech" "India" founder 2025',
        'site:linkedin.com/in "women\'s health" "India" founder 2024',
        'site:linkedin.com/in "fertility" "India" founder startup 2024',
        'site:linkedin.com/in "maternal health" "India" founder 2024',

        # Diagnostics / biotech
        'site:linkedin.com/in "diagnostics" "India" founder startup 2024',
        'site:linkedin.com/in "diagnostics" "India" founder startup 2025',
        'site:linkedin.com/in "biotech" "India" founder startup 2024',
        'site:linkedin.com/in "genomics" "India" founder startup 2024',
        'site:linkedin.com/in "pathology" "India" founder startup 2024',

        # Fitness / nutrition
        'site:linkedin.com/in "fitness" "India" founder startup 2024',
        'site:linkedin.com/in "fitness" "India" founder startup 2025',
        'site:linkedin.com/in "nutrition" "India" founder startup 2024',
        'site:linkedin.com/in "nutraceutical" "India" founder 2024',

        # Elder care
        'site:linkedin.com/in "eldercare" "India" founder 2024',
        'site:linkedin.com/in "elder care" "India" founder 2024',
        'site:linkedin.com/in "senior care" "India" founder startup 2024',

        # Hospital / clinic / pharma
        'site:linkedin.com/in "hospital" "startup" "India" founder 2024',
        'site:linkedin.com/in "pharmacy" "startup" "India" founder 2024',
        'site:linkedin.com/in "pharma tech" "India" founder 2024',
        'site:linkedin.com/in "clinical" "startup" "India" founder 2024',
        'site:linkedin.com/in "oncology" "startup" "India" founder 2024',
        'site:linkedin.com/in "radiology" "AI" "India" founder 2024',
        'site:linkedin.com/in "dental" "startup" "India" founder 2024',

        # AI in health
        'site:linkedin.com/in "AI" "healthcare" "India" founder 2024',
        'site:linkedin.com/in "AI" "healthcare" "India" founder 2025',
        'site:linkedin.com/in "AI" "diagnostics" "India" founder 2024',
        'site:linkedin.com/in "AI" "mental health" "India" founder 2024',

        # "Building for India" health intent
        'site:linkedin.com/in "building for India" health founder 2024',
        'site:linkedin.com/in "building for India" health founder 2025',
        'site:linkedin.com/in "India-first" health OR healthcare founder 2024',
        'site:linkedin.com/in "affordable healthcare" "India" founder 2024',
        'site:linkedin.com/in "tier 2" OR "tier 3" healthcare "India" founder 2024',

        # City-specific health
        *[f'site:linkedin.com/in "health" "founder" "{city}" startup 2024' for city in INDIA_CITIES[:6]],
        *[f'site:linkedin.com/in "healthcare" "founder" "{city}" startup 2025' for city in INDIA_CITIES[:4]],

        # Genomics / precision medicine
        'site:linkedin.com/in "genomics" "India" founder startup 2024',
        'site:linkedin.com/in "precision medicine" "India" founder 2025',
        'site:linkedin.com/in "longevity" "India" founder startup 2025',

        # Hospital / clinic tech
        'site:linkedin.com/in "hospital tech" "India" founder 2024',
        'site:linkedin.com/in "clinic management" "India" founder 2024',
        'site:linkedin.com/in "EMR" OR "EHR" "India" founder startup 2024',
        'site:linkedin.com/in "health insurance" "India" founder startup 2025',

        # AI health
        'site:linkedin.com/in "AI radiology" OR "AI diagnostics" "India" founder 2025',
        'site:linkedin.com/in "medical AI" "India" founder startup 2025',
        'site:linkedin.com/in "AI drug discovery" "India" founder 2024',
    ]
    return _collect(queries, "healthtech_linkedin")


# ── Ex-employee & institution founders (cross-sector) ─────────────────────────

def search_ex_employee_founders() -> list[dict]:
    """Ex-employees of top Indian/global companies who became founders."""
    founders = []
    all_companies = list(dict.fromkeys(MAFIA_COMPANIES + TOP_COMPANIES))
    for company in all_companies:
        query = GOOGLE_DORK_TEMPLATES["linkedin_ex_employee"].format(company=company)
        print(f"  Searching ex-{company} founders...")
        for r in google_search(query):
            if "linkedin.com/in/" in r["url"]:
                founders.append({
                    "linkedin_url": r["url"].split("?")[0],
                    "title":        r["title"],
                    "snippet":      r["snippet"],
                    "query_source": f"ex_{company}",
                })
    return founders


def search_institution_founders() -> list[dict]:
    """IIT / IIM / BITS / international alumni who founded India startups."""
    founders = []
    for inst in PREMIER_INSTITUTIONS:
        query = GOOGLE_DORK_TEMPLATES["iit_founder"].format(institution=inst)
        print(f"  Searching {inst} founders...")
        for r in google_search(query):
            if "linkedin.com/in/" in r["url"]:
                founders.append({
                    "linkedin_url": r["url"].split("?")[0],
                    "title":        r["title"],
                    "snippet":      r["snippet"],
                    "query_source": f"institution_{inst}",
                })
    return founders


def search_general_india_founders() -> list[dict]:
    """Broad India founder signals not captured by sector-specific queries."""
    queries = [
        # "I'm building" generic
        'site:linkedin.com/in "I\'m building" "India" 2024',
        'site:linkedin.com/in "I\'m building" "India" 2025',
        'site:linkedin.com/in "we are building" "India" founder 2024',
        'site:linkedin.com/in "we are building" "India" founder 2025',

        # Stealth / pre-launch India
        'site:linkedin.com/in "stealth" founder "India" startup 2024',
        'site:linkedin.com/in "stealth" founder "India" startup 2025',
        'site:linkedin.com/in "pre-launch" founder "India" 2025',

        # Funding signals
        'site:linkedin.com/in "pre-seed" founder "India" 2024',
        'site:linkedin.com/in "pre-seed" founder "India" 2025',
        'site:linkedin.com/in "raised seed" founder "India" 2024',
        'site:linkedin.com/in "raised seed" founder "India" 2025',
        'site:linkedin.com/in "angel funded" founder "India" 2024',

        # "Quit to build"
        'site:linkedin.com/in "left" OR "quit" "to build" founder "India" 2024',
        'site:linkedin.com/in "left" OR "quit" "to build" founder "India" 2025',
        'site:linkedin.com/in "quit my job" "building" "India" 2025',

        # Bharat / rural / vernacular focus
        'site:linkedin.com/in "Bharat" "founder" startup 2024',
        'site:linkedin.com/in "Bharat" "founder" startup 2025',
        'site:linkedin.com/in "rural India" founder startup 2024',
        'site:linkedin.com/in "vernacular" founder "India" 2024',
        'site:linkedin.com/in "regional language" founder "India" 2024',

        # YC / Antler / SURGE backed Indians
        'site:linkedin.com/in "YC" OR "Y Combinator" "India" founder 2024',
        'site:linkedin.com/in "YC" OR "Y Combinator" "India" founder 2025',
        'site:linkedin.com/in "Antler" "India" founder 2024',
        'site:linkedin.com/in "Antler" "India" founder 2025',
        'site:linkedin.com/in "SURGE" "India" founder 2024',
        'site:linkedin.com/in "100X.VC" "India" founder 2024',

        # More accelerators / incubators
        'site:linkedin.com/in "T-Hub" "India" founder startup 2024',
        'site:linkedin.com/in "T-Hub" "India" founder startup 2025',
        'site:linkedin.com/in "CIIE" "India" founder startup 2024',
        'site:linkedin.com/in "NSRCEL" "India" founder startup 2024',
        'site:linkedin.com/in "Axilor" "India" founder startup 2024',
        'site:linkedin.com/in "Better Capital" "India" founder 2024',
        'site:linkedin.com/in "Better Capital" "India" founder 2025',
        'site:linkedin.com/in "Titan Capital" "India" founder 2024',
        'site:linkedin.com/in "Fireside Ventures" "India" founder 2024',
        'site:linkedin.com/in "India Quotient" "India" founder 2024',

        # Forbes 30U30 / Hurun Under-35
        'site:linkedin.com/in "Forbes 30 Under 30" "India" founder 2024',
        'site:linkedin.com/in "Hurun" "Under 35" "India" founder startup 2024',
        'site:linkedin.com/in "Forbes 30 Under 30" "India" founder 2025',

        # Deeptech / space / defense
        'site:linkedin.com/in "deeptech" "India" founder startup 2024',
        'site:linkedin.com/in "spacetech" "India" founder startup 2024',
        'site:linkedin.com/in "defence tech" OR "defense tech" "India" founder 2025',
        'site:linkedin.com/in "semiconductor" "India" founder startup 2025',

        # Social impact / Bharat-focused
        'site:linkedin.com/in "impact startup" "India" founder 2024',
        'site:linkedin.com/in "social enterprise" "India" founder 2024',
        'site:linkedin.com/in "fintech for Bharat" founder startup 2025',
    ]
    return _collect(queries, "general_india_linkedin")


def deduplicate(founders: list[dict]) -> list[dict]:
    """Remove duplicate LinkedIn URLs."""
    seen = set()
    unique = []
    for f in founders:
        url = f["linkedin_url"].rstrip("/").lower()
        if url not in seen:
            seen.add(url)
            unique.append(f)
    return unique


def run():
    """Main entry point."""
    print("\n=== LinkedIn Scraper (Google Dorking) ===\n")

    all_founders = []

    print("[1/6] Consumer AI founders (India)...")
    all_founders.extend(search_consumer_ai())

    print(f"\n[2/6] Consumer Tech founders (India)...")
    all_founders.extend(search_consumer_tech())

    print(f"\n[3/6] HealthTech founders (India)...")
    all_founders.extend(search_healthtech())

    print(f"\n[4/6] General India founder signals...")
    all_founders.extend(search_general_india_founders())

    print(f"\n[5/6] Ex-employee founders ({len(list(dict.fromkeys(MAFIA_COMPANIES + TOP_COMPANIES)))} companies)...")
    all_founders.extend(search_ex_employee_founders())

    print(f"\n[6/6] Institution founders ({len(PREMIER_INSTITUTIONS)} institutions)...")
    all_founders.extend(search_institution_founders())

    unique = deduplicate(all_founders)
    print(f"\nTotal unique LinkedIn profiles found: {len(unique)}")

    output_path = Path(__file__).parent.parent / "data" / "linkedin_raw.json"
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(unique, f, indent=2, ensure_ascii=False)
    print(f"Saved to {output_path}")

    return unique


if __name__ == "__main__":
    run()
