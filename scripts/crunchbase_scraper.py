"""
Deal Flow Pipeline - Crunchbase Scraper (Free Tier)
Scrapes Crunchbase public search pages for early-stage Indian startups.
No API key needed - uses Google dorking on Crunchbase pages.
"""

import json
from pathlib import Path

from config import SECTOR_KEYWORDS
from utils import web_search as google_search  # DDG-primary, Google fallback


def search_crunchbase_startups() -> list[dict]:
    """Google dork Crunchbase for early-stage Indian startups."""
    queries = [
        'site:crunchbase.com/organization "India" "consumer" "AI" "seed" 2024',
        'site:crunchbase.com/organization "India" "health" "seed" 2024',
        'site:crunchbase.com/organization "India" "consumer" "pre-seed" 2024',
        'site:crunchbase.com/organization "Bengaluru" "AI" "seed" 2024',
        'site:crunchbase.com/organization "Mumbai" "consumer" "seed" 2024 2025',
        'site:crunchbase.com/organization "Delhi" "health" "seed" 2024',
        'site:crunchbase.com/organization "India" "AI" "unfunded" 2024',
        'site:crunchbase.com/organization "India" "consumer tech" "pre-seed" 2025',
        'site:crunchbase.com/organization "India" "mental health" "seed" 2024',
        'site:crunchbase.com/organization "India" "edtech" "AI" "seed" 2024',
    ]

    results = []
    for q in queries:
        print(f"  Searching: {q[:60]}...")
        hits = google_search(q, 10)
        for h in hits:
            if "crunchbase.com/organization/" in h["url"]:
                org_slug = h["url"].split("/organization/")[-1].split("/")[0].split("?")[0]
                results.append({
                    "crunchbase_url": h["url"].split("?")[0],
                    "org_slug": org_slug,
                    "title": h["title"],
                    "snippet": h["snippet"],
                    "source": "crunchbase_google"
                })

    # Deduplicate by org_slug
    seen = set()
    unique = []
    for r in results:
        if r["org_slug"] not in seen:
            seen.add(r["org_slug"])
            unique.append(r)

    return unique


def run():
    """Main entry point."""
    print("\n=== Crunchbase Scraper (Google Dorking) ===\n")

    results = search_crunchbase_startups()
    print(f"\nTotal unique Crunchbase orgs found: {len(results)}")

    output_path = Path(__file__).parent.parent / "data" / "crunchbase_raw.json"
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Saved to {output_path}")

    return results


if __name__ == "__main__":
    run()
