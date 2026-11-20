"""
Deal Flow Pipeline - Google News & Media Scraper
Finds early-stage Indian startups from funding announcements in:
  Inc42, YourStory, Economic Times, Mint, Business Standard,
  TechCrunch (India), Entrackr, The Ken, VCCircle, Moneycontrol

Uses Google News dorking - no API keys needed.
Extracts: startup name, founder, amount raised, sector, city.
"""

import json
import re
from pathlib import Path

from utils import web_search as google_search  # DDG-primary, Google fallback

# ── Query banks ───────────────────────────────────────────────────────────────

# High-signal funding news queries
FUNDING_QUERIES = [
    # Pre-seed & seed - India, all sectors
    ('"pre-seed" "startup" "India" "raises" OR "raised" 2024', "news:preseed"),
    ('"pre-seed" "startup" "India" "raises" OR "raised" 2025', "news:preseed"),
    ('"seed round" "startup" "India" "raises" OR "raised" 2024', "news:seed"),
    ('"seed round" "startup" "India" "raises" OR "raised" 2025', "news:seed"),
    ('"angel round" "India" startup founder 2024 2025', "news:angel"),
    ('"seed funding" India startup AI health consumer 2024', "news:seed"),
    ('"seed funding" India startup AI health consumer 2025', "news:seed"),

    # Inc42 - India's top startup news source
    ('site:inc42.com "raises" "pre-seed" OR "seed" India startup 2024', "inc42:seed"),
    ('site:inc42.com "raises" "pre-seed" OR "seed" India startup 2025', "inc42:seed"),
    ('site:inc42.com "funding" India startup "Consumer AI" OR "healthtech" 2024', "inc42:healthtech_ai"),
    ('site:inc42.com "funding" India startup "Consumer AI" OR "healthtech" 2025', "inc42:healthtech_ai"),
    ('site:inc42.com "funding" India startup "fintech" OR "edtech" 2024 2025', "inc42:fintech_edtech"),
    ('site:inc42.com "launches" startup India founder 2024 2025', "inc42:launch"),

    # YourStory
    ('site:yourstory.com "raises" "seed" OR "pre-seed" India startup 2024', "yourstory:seed"),
    ('site:yourstory.com "raises" "seed" OR "pre-seed" India startup 2025', "yourstory:seed"),
    ('site:yourstory.com India startup "AI" founder "funding" 2024 2025', "yourstory:ai"),
    ('site:yourstory.com India startup "healthtech" founder "funding" 2024 2025', "yourstory:health"),

    # Entrackr - tracks early rounds closely
    ('site:entrackr.com "seed" OR "pre-seed" India startup 2024 2025', "entrackr:seed"),
    ('site:entrackr.com "funding" India startup 2024 2025', "entrackr:funding"),

    # Economic Times & Mint
    ('site:economictimes.indiatimes.com "startup" "India" "seed" OR "pre-seed" raises 2024 2025', "et:seed"),
    ('site:livemint.com "startup" "India" "seed" raises 2024 2025', "mint:seed"),

    # VCCircle - VC-focused India news
    ('site:vccircle.com "seed" OR "pre-seed" India startup raises 2024 2025', "vccircle:seed"),
    ('site:vccircle.com "Series A" India startup raises 2024 2025', "vccircle:series_a"),

    # TechCrunch India
    ('site:techcrunch.com "India" "startup" "seed" OR "pre-seed" 2024 2025', "techcrunch:india_seed"),
    ('site:techcrunch.com "India" "startup" "Series A" 2024 2025', "techcrunch:india_series_a"),

    # Business Standard
    ('site:business-standard.com startup India "seed" OR "pre-seed" raises 2024 2025', "bs:seed"),

    # The Ken & Moneycontrol
    ('site:the-ken.com India startup funding 2024 2025', "theken:funding"),
    ('site:moneycontrol.com startup India "seed" OR "pre-seed" raises 2024 2025', "moneycontrol:seed"),

    # Forbes India
    ('site:forbesindia.com startup India seed "raises" OR "funding" 2024 2025', "forbes_india:seed"),
    ('site:forbesindia.com "30 Under 30" India startup founder 2024 2025', "forbes_india:30u30"),

    # Business Today
    ('site:businesstoday.in startup India "seed" OR "pre-seed" raises 2024 2025', "bt:seed"),
    ('site:businesstoday.in startup India AI health consumer funded 2024 2025', "bt:funded"),

    # Financial Express
    ('site:financialexpress.com startup India "seed" OR "pre-seed" raises 2024 2025', "fe:seed"),

    # Rest of World - India tech coverage
    ('site:restofworld.org India startup AI health consumer 2024 2025', "row:india"),

    # NDTV Profit
    ('site:ndtvprofit.com startup India "funding" "seed" OR "pre-seed" 2024 2025', "ndtv:funding"),

    # Startup Talky
    ('site:startuptalky.com India startup founder funding AI health consumer 2024 2025', "startuptalky:funding"),
]

# Stealth / launch signals from news
LAUNCH_QUERIES = [
    ('"India" "startup" "launches" "AI" OR "healthtech" OR "consumer" 2024 2025', "news:launch"),
    ('"India" startup "goes live" OR "launched" consumer AI health 2024 2025', "news:launch"),
    ('site:inc42.com "launched" startup India 2024 2025', "inc42:launch"),
    ('site:yourstory.com "launched" startup India AI health consumer 2025', "yourstory:launch"),
    ('"stealth" "startup" "India" "exits stealth" 2024 2025', "news:stealth_exit"),
    ('"India" "startup" "exits stealth" AI health consumer 2024 2025', "news:stealth_exit"),
]

# Sector-specific news
SECTOR_QUERIES = [
    # Consumer AI
    ('"India" "AI startup" "funding" OR "raises" 2024 2025', "news:ai"),
    ('"India" "generative AI" startup "funding" 2024 2025', "news:genai"),
    ('"India" "LLM" startup "funding" OR "raises" 2024 2025', "news:llm"),
    ('site:inc42.com "AI" startup India 2024 2025 funding raises', "inc42:ai"),
    ('site:yourstory.com "AI" startup India 2025 funding', "yourstory:ai_2025"),

    # HealthTech
    ('"India" "healthtech" startup "funding" OR "raises" 2024 2025', "news:health"),
    ('"India" "medtech" startup "funding" OR "raises" 2024 2025', "news:medtech"),
    ('"India" "mental health" startup "funding" 2024 2025', "news:mental_health"),
    ('site:inc42.com "healthtech" startup India 2024 2025', "inc42:health"),

    # Consumer Tech
    ('"India" "D2C" startup "funding" OR "raises" 2024 2025', "news:d2c"),
    ('"India" "fintech" startup "seed" OR "pre-seed" 2024 2025', "news:fintech"),
    ('"India" "edtech" startup "funding" 2024 2025', "news:edtech"),
    ('"India" "quick commerce" startup "funding" 2024 2025', "news:qcommerce"),

    # City-specific news
    ('"Bengaluru" startup "seed" OR "pre-seed" "funding" 2024 2025', "news:bengaluru"),
    ('"Mumbai" startup "seed" OR "pre-seed" "funding" 2024 2025', "news:mumbai"),
    ('"Delhi" startup "seed" OR "pre-seed" "funding" 2024 2025', "news:delhi"),
    ('"Hyderabad" startup "seed" OR "pre-seed" "funding" 2024 2025', "news:hyderabad"),
    ('"Chennai" startup "seed" OR "pre-seed" "funding" 2024 2025', "news:chennai"),
    ('"Pune" startup "seed" OR "pre-seed" "funding" 2024 2025', "news:pune"),

    # Emerging themes
    ('"India" "agentic AI" startup "funding" OR "raises" 2024 2025', "news:agentic_ai"),
    ('"India" "AI agents" startup "funding" 2025', "news:ai_agents"),
    ('"India" "climate tech" startup "funding" OR "raises" 2024 2025', "news:climate"),
    ('"India" "cleantech" startup "seed" OR "funding" 2024 2025', "news:cleantech"),
    ('"India" "agritech" startup "seed" OR "funding" 2024 2025', "news:agritech"),
    ('"India" "proptech" startup "seed" OR "funding" 2024 2025', "news:proptech"),
    ('"India" "insurtech" startup "seed" OR "funding" 2024 2025', "news:insurtech"),
    ('"India" "wealthtech" startup "seed" OR "funding" 2024 2025', "news:wealthtech"),
    ('"India" "spacetech" startup "seed" OR "funding" 2024 2025', "news:spacetech"),
    ('"India" "legaltech" startup "seed" OR "funding" 2024 2025', "news:legaltech"),

    # IIT/IIM spinout news
    ('"IIT" OR "IIM" India startup spinout founded "funding" 2024 2025', "news:iit_iim_spinout"),
    ('"incubated at IIT" OR "incubated at IIM" India startup 2024 2025', "news:iit_incubated"),
]

ALL_QUERIES = FUNDING_QUERIES + LAUNCH_QUERIES + SECTOR_QUERIES


# ── Extraction helpers ─────────────────────────────────────────────────────────

# Patterns to extract funding amounts
AMOUNT_RE = re.compile(
    r"\$?([\d,]+(?:\.\d+)?)\s*(million|mn|lakh|crore|cr|bn|billion|k)\b",
    re.IGNORECASE
)

# City signals
CITY_MAP = {
    "bengaluru": "Bengaluru", "bangalore": "Bengaluru",
    "mumbai": "Mumbai", "bombay": "Mumbai",
    "delhi": "Delhi", "new delhi": "Delhi", "gurugram": "Gurugram",
    "noida": "Noida", "hyderabad": "Hyderabad",
    "pune": "Pune", "chennai": "Chennai", "kolkata": "Kolkata",
    "ahmedabad": "Ahmedabad", "jaipur": "Jaipur",
}

# Funding stage signals
STAGE_MAP = {
    "pre-seed": "Pre-Seed", "preseed": "Pre-Seed",
    "seed": "Seed", "angel": "Angel",
    "series a": "Series A", "series b": "Series B",
    "series c": "Series C",
}


def extract_startup_name(title: str, snippet: str) -> str:
    """Best-effort startup name extraction from article title / snippet."""
    # Pattern 1: "StartupName raises/secures/closes $X"
    m = re.search(
        r"^([A-Z][A-Za-z0-9\.\-\s]{1,40}?)\s+(?:raises?|secures?|closes?|bags?|gets?)\b",
        title
    )
    if m:
        return m.group(1).strip()

    # Pattern 2: "StartupName launches / unveils / debuts"
    m = re.search(r"^([A-Z][A-Za-z0-9\.\-\s]{1,40}?)\s+(?:launches?|unveils?|debuts?|goes live)\b", title)
    if m:
        return m.group(1).strip()

    # Pattern 3: "Founder/s of StartupName ..."
    m = re.search(r"(?:founder|co-founder|ceo)\s+of\s+([A-Z][A-Za-z0-9\.\-]{2,30})", title, re.IGNORECASE)
    if m:
        return m.group(1).strip()

    # Pattern 4: "StartupName, a [city/India] [sector] startup"
    m = re.search(
        r"^([A-Z][A-Za-z0-9\.\-]{2,30}),\s+(?:a|an)\s+(?:India[n\-]?\s+)?(?:\w+\s+)?startup\b",
        title
    )
    if m:
        return m.group(1).strip()

    # Pattern 5: "[India] startup StartupName"
    m = re.search(r"(?:India[n]?\s+startup|startup)\s+([A-Z][A-Za-z0-9\.\-]{2,30})\b", title)
    if m:
        return m.group(1).strip()

    # Pattern 6: "StartupName gets/receives funding"
    m = re.search(
        r"^([A-Z][A-Za-z0-9\.\-\s]{1,40}?)\s+(?:gets?|receives?|lands?|wins?)\s+(?:funding|investment|backing)\b",
        title, re.IGNORECASE
    )
    if m:
        return m.group(1).strip()

    # Fallback: try snippet with same patterns
    for text in [snippet]:
        m = re.search(
            r"^([A-Z][A-Za-z0-9\.\-\s]{1,40}?)\s+(?:raises?|secures?|launched?|funding)\b",
            text
        )
        if m:
            return m.group(1).strip()

    return ""


def extract_city(text: str) -> str | None:
    """Extract city from text."""
    text_lower = text.lower()
    for key, city in CITY_MAP.items():
        if key in text_lower:
            return city
    return None


def extract_funding_stage(text: str) -> str | None:
    """Extract funding stage from text."""
    text_lower = text.lower()
    for key, stage in STAGE_MAP.items():
        if key in text_lower:
            return stage
    return None


def extract_year(text: str) -> int:
    """Extract founding/funding year from text."""
    m = re.search(r"\b(202[2-5])\b", text)
    return int(m.group(1)) if m else 2024


def parse_result(hit: dict, source_tag: str) -> dict:
    """Convert a raw search hit into a structured startup record."""
    title = hit.get("title", "")
    snippet = hit.get("snippet", "")
    combined = f"{title} {snippet}"

    startup_name = extract_startup_name(title, snippet)
    city = extract_city(combined)
    funding_stage = extract_funding_stage(combined)
    year = extract_year(combined)

    return {
        "startup_name":  startup_name or "Unknown",
        "founder_name":  "",
        "linkedin_url":  None,
        "website":       hit.get("url"),
        "one_liner":     snippet[:120],
        "snippet":       snippet,
        "title":         title,
        "source":        f"news:{source_tag}",
        "founded_year":  year,
        "city":          city,
        "funding_stage": funding_stage,
        "query_source":  source_tag,
    }


def run():
    """Main entry point."""
    print("\n=== Google News / Media Scraper ===\n")

    all_results = []
    seen_urls: set[str] = set()

    for query, tag in ALL_QUERIES:
        print(f"  [{tag}] {query[:70]}...")
        hits = google_search(query, num_results=20)
        for h in hits:
            url_key = h["url"].split("?")[0].lower()
            if url_key in seen_urls:
                continue
            seen_urls.add(url_key)
            all_results.append(parse_result(h, tag))

    # Filter out hits with no extractable startup name
    named = [r for r in all_results if r["startup_name"] != "Unknown"]
    unnamed = [r for r in all_results if r["startup_name"] == "Unknown"]

    print(f"\nTotal hits: {len(all_results)}  |  Named: {len(named)}  |  Profile-only: {len(unnamed)}")

    output_path = Path(__file__).parent.parent / "data" / "news_raw.json"
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"Saved to {output_path}")

    return all_results


if __name__ == "__main__":
    run()
