"""
Deal Flow Pipeline - Tracxn Scraper (Free Tier)
Scrapes Tracxn public company pages via Google dorking.
No API key needed.
"""

import json
from pathlib import Path

from utils import web_search as google_search  # DDG-primary, Google fallback


def search_tracxn_startups() -> list[dict]:
    """Google dork Tracxn for early-stage Indian startups."""
    queries = [
        'site:tracxn.com/d/companies "India" "consumer AI" seed',
        'site:tracxn.com/d/companies "India" "healthtech" seed unfunded',
        'site:tracxn.com/d/companies "India" "consumer tech" pre-seed 2024',
        'site:tracxn.com/d/explore "consumer-ai-startups-in-india"',
        'site:tracxn.com/d/explore "healthtech-startups-in-india"',
        'site:tracxn.com/d/explore "consumer-tech-startups-in-india"',
        'site:tracxn.com "India" "unfunded" "consumer" "AI" 2024',
        'site:tracxn.com "India" "bootstrapped" "consumer" 2024',
    ]

    results = []
    for q in queries:
        print(f"  Searching: {q[:60]}...")
        hits = google_search(q, 10)
        for h in hits:
            if "tracxn.com" in h["url"]:
                results.append({
                    "tracxn_url": h["url"].split("?")[0],
                    "title": h["title"],
                    "snippet": h["snippet"],
                    "source": "tracxn_google"
                })

    # Deduplicate by URL
    seen = set()
    unique = []
    for r in results:
        if r["tracxn_url"] not in seen:
            seen.add(r["tracxn_url"])
            unique.append(r)

    return unique


def run():
    """Main entry point."""
    print("\n=== Tracxn Scraper (Google Dorking) ===\n")

    results = search_tracxn_startups()
    print(f"\nTotal unique Tracxn results: {len(results)}")

    output_path = Path(__file__).parent.parent / "data" / "tracxn_raw.json"
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Saved to {output_path}")

    return results


if __name__ == "__main__":
    run()
