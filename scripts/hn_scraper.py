"""
Deal Flow Pipeline - Hacker News Algolia Scraper
Finds Indian founders announcing startups on Hacker News (Show HN / Ask HN).

Uses the free HN Algolia API - no key, no rate limit (within reason).
API docs: https://hn.algolia.com/api
"""

import json
import time
from pathlib import Path

try:
    import requests
except ImportError:
    print("Install dependency: pip install requests")
    exit(1)

from config import REQUEST_DELAY_SECONDS

HN_SEARCH_URL = "https://hn.algolia.com/api/v1/search"
HN_SEARCH_BY_DATE_URL = "https://hn.algolia.com/api/v1/search_by_date"

# Unix timestamp: Jan 1 2024
AFTER_JAN_2024 = 1704067200
# Unix timestamp: Jan 1 2023 (wider net)
AFTER_JAN_2023 = 1672531200


# ── Query groups ──────────────────────────────────────────────────────────────

# Show HN posts by Indian founders
SHOW_HN_QUERIES = [
    # Consumer AI
    ("Show HN India AI startup", "show_hn:ai"),
    ("Show HN India artificial intelligence", "show_hn:ai"),
    ("Show HN India LLM generative AI", "show_hn:genai"),
    ("Show HN India AI agent", "show_hn:ai_agent"),
    ("Show HN India machine learning", "show_hn:ml"),
    ("Show HN India voice AI vernacular", "show_hn:voice_ai"),

    # HealthTech
    ("Show HN India health startup", "show_hn:health"),
    ("Show HN India healthcare AI", "show_hn:health_ai"),
    ("Show HN India mental health", "show_hn:mental_health"),
    ("Show HN India medtech diagnostics", "show_hn:medtech"),
    ("Show HN India telemedicine", "show_hn:telemedicine"),

    # Consumer Tech
    ("Show HN India consumer startup", "show_hn:consumer"),
    ("Show HN India fintech", "show_hn:fintech"),
    ("Show HN India edtech", "show_hn:edtech"),
    ("Show HN India D2C", "show_hn:d2c"),
    ("Show HN India marketplace", "show_hn:marketplace"),
    ("Show HN India SaaS India", "show_hn:saas"),
    ("Show HN India mobile app", "show_hn:mobile"),

    # IIT / IIM founders
    ("Show HN IIT founder India", "show_hn:iit"),
    ("Show HN IIM founder India", "show_hn:iim"),
    ("Show HN BITS Pilani startup", "show_hn:bits"),
]

# Ask HN posts about India startup ecosystem
ASK_HN_QUERIES = [
    ("Ask HN building startup India", "ask_hn:building"),
    ("Ask HN launched India startup", "ask_hn:launched"),
    ("Ask HN India startup fundraising", "ask_hn:fundraising"),
    ("Ask HN India YC founder", "ask_hn:yc"),
]

# Broad HN posts (story type) mentioning India founders
STORY_QUERIES = [
    ("India startup raises seed funding AI", "hn:seed_ai"),
    ("India founder building AI startup", "hn:ai_founder"),
    ("India healthtech startup raises", "hn:healthtech"),
    ("India consumer startup launched", "hn:consumer"),
    ("Bengaluru startup AI raises", "hn:bengaluru"),
    ("Mumbai startup AI raises", "hn:mumbai"),
    ("Indian founder YC W24 W25", "hn:yc"),
    ("India startup Antler", "hn:antler"),
    ("India startup pre-seed seed raises 2024", "hn:preseed"),
    ("India startup pre-seed seed raises 2025", "hn:preseed_25"),
]


# ── API helpers ───────────────────────────────────────────────────────────────

def hn_search(
    query: str,
    tags: str = "story",
    num_results: int = 20,
    after_ts: int = AFTER_JAN_2024,
    by_date: bool = False,
) -> list[dict]:
    """
    Call HN Algolia API and return list of raw hits.
    tags: "story", "show_hn", "ask_hn", "comment"
    """
    url = HN_SEARCH_BY_DATE_URL if by_date else HN_SEARCH_URL
    params = {
        "query":          query,
        "tags":           tags,
        "hitsPerPage":    num_results,
        "numericFilters": f"created_at_i>{after_ts}",
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        hits = resp.json().get("hits", [])
        time.sleep(0.5)  # HN API is lenient but be polite
        return hits
    except Exception as e:
        print(f"  [HN] Search failed for '{query}': {e}")
        return []


def hit_to_record(hit: dict, source_tag: str) -> dict:
    """Convert an HN API hit into a pipeline-compatible record."""
    title   = hit.get("title", "") or ""
    url     = hit.get("url", "") or f"https://news.ycombinator.com/item?id={hit.get('objectID','')}"
    snippet = hit.get("story_text", "") or ""
    author  = hit.get("author", "")

    # Best-effort startup name from title
    import re
    startup_name = "Unknown"
    # "Show HN: StartupName – description"
    m = re.search(r"(?:Show HN|Ask HN)[:\s]+([A-Z][A-Za-z0-9\.\-\s]{2,40}?)(?:\s*[–\-–]|\s*$)", title)
    if m:
        startup_name = m.group(1).strip()
    else:
        # "StartupName raises ..." / "StartupName launches ..."
        m = re.search(
            r"^([A-Z][A-Za-z0-9\.\-]{2,30})\s+(?:raises?|launches?|secures?|unveils?)\b",
            title
        )
        if m:
            startup_name = m.group(1).strip()

    return {
        "startup_name":  startup_name,
        "founder_name":  author,
        "linkedin_url":  None,
        "website":       url if url.startswith("http") and "ycombinator" not in url else None,
        "one_liner":     title[:120],
        "snippet":       snippet[:200],
        "source":        f"hn:{source_tag}",
        "founded_year":  2024,
        "query_source":  source_tag,
        "hn_url":        f"https://news.ycombinator.com/item?id={hit.get('objectID','')}",
    }


# ── Main scrapers ─────────────────────────────────────────────────────────────

def scrape_show_hn() -> list[dict]:
    """Scrape Show HN posts from Indian founders."""
    print("  Scraping Show HN (India)...")
    results = []
    for query, tag in SHOW_HN_QUERIES:
        hits = hn_search(query, tags="show_hn", num_results=20, after_ts=AFTER_JAN_2023)
        for h in hits:
            results.append(hit_to_record(h, tag))
    return results


def scrape_ask_hn() -> list[dict]:
    """Scrape Ask HN posts from Indian founders."""
    print("  Scraping Ask HN (India)...")
    results = []
    for query, tag in ASK_HN_QUERIES:
        hits = hn_search(query, tags="ask_hn", num_results=10, after_ts=AFTER_JAN_2023)
        for h in hits:
            results.append(hit_to_record(h, tag))
    return results


def scrape_hn_stories() -> list[dict]:
    """Scrape general HN stories about India startups."""
    print("  Scraping HN stories (India startups)...")
    results = []
    for query, tag in STORY_QUERIES:
        hits = hn_search(query, tags="story", num_results=20, after_ts=AFTER_JAN_2023)
        for h in hits:
            results.append(hit_to_record(h, tag))
    return results


def run() -> list[dict]:
    """Main entry point."""
    print("\n=== Hacker News Algolia Scraper ===\n")

    all_results = []

    all_results.extend(scrape_show_hn())
    all_results.extend(scrape_ask_hn())
    all_results.extend(scrape_hn_stories())

    # Deduplicate by HN URL
    seen: set[str] = set()
    unique = []
    for r in all_results:
        key = r.get("hn_url", r.get("website", ""))
        if key and key not in seen:
            seen.add(key)
            unique.append(r)

    named   = [r for r in unique if r["startup_name"] != "Unknown"]
    unnamed = [r for r in unique if r["startup_name"] == "Unknown"]
    print(f"\nTotal HN hits: {len(unique)}  |  Named: {len(named)}  |  Author-only: {len(unnamed)}")

    output_path = Path(__file__).parent.parent / "data" / "hn_raw.json"
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(unique, f, indent=2, ensure_ascii=False)
    print(f"Saved to {output_path}")

    return unique


if __name__ == "__main__":
    run()
