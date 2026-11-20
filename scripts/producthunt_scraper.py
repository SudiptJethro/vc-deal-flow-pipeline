"""
Deal Flow Pipeline - Product Hunt Scraper
Finds Indian startups launched on Product Hunt in 2024-2026.
Uses the free Product Hunt API (GraphQL).
"""

import json
import time
from pathlib import Path
from datetime import datetime, timedelta

try:
    import requests
except ImportError:
    print("Install dependency: pip install requests")
    exit(1)

from config import SECTOR_KEYWORDS, EXCLUDED_STARTUPS, REQUEST_DELAY_SECONDS
from utils import web_search


# Product Hunt GraphQL API (free, needs developer token)
# Get one at: https://www.producthunt.com/v2/oauth/applications
PH_API_URL = "https://api.producthunt.com/v2/api/graphql"


def search_producthunt_google() -> list[dict]:
    """Fallback: search Product Hunt for Indian makers via the CF Worker / DDG.

    Uses web_search (CF Worker → DDG) instead of raw Google scraping.
    Raw Google requests always 429 from GH Actions IPs.
    site:producthunt.com is fine here - PH allows search-engine indexing.
    """
    queries = [
        'site:producthunt.com "India" "AI" "launched" 2024',
        'site:producthunt.com "India" "health" "launched" 2024',
        'site:producthunt.com "India" "consumer" "launched" 2025',
        'site:producthunt.com "Bengaluru" OR "Mumbai" OR "Delhi" "AI" 2024',
        'site:producthunt.com "Indian founder" "launched" 2024 2025',
    ]

    seen: set[str] = set()
    results: list[dict] = []

    for q in queries:
        print(f"  Searching: {q[:60]}...")
        for h in web_search(q):
            url = h.get("url", "")
            if "producthunt.com/posts/" in url:
                key = url.split("?")[0].lower()
                if key not in seen:
                    seen.add(key)
                    results.append({
                        "ph_url":   url.split("?")[0],
                        "title":    h.get("title", ""),
                        "snippet":  h.get("snippet", ""),
                        "source":   "producthunt_google",
                    })

    return results


def search_producthunt_api(token: str) -> list[dict]:
    """
    Use Product Hunt GraphQL API to find Indian launches.
    Requires a developer token from https://www.producthunt.com/v2/oauth/applications
    """
    query = """
    query($cursor: String) {
      posts(first: 20, after: $cursor, order: NEWEST) {
        edges {
          node {
            id
            name
            tagline
            url
            votesCount
            createdAt
            makers {
              name
              headline
              profileImage
              websiteUrl
            }
            topics {
              edges {
                node {
                  name
                }
              }
            }
          }
        }
        pageInfo {
          hasNextPage
          endCursor
        }
      }
    }
    """

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    results = []
    cursor = None
    pages = 0
    max_pages = 10  # Limit to avoid hitting rate limits

    while pages < max_pages:
        variables = {"cursor": cursor} if cursor else {}
        try:
            resp = requests.post(
                PH_API_URL,
                json={"query": query, "variables": variables},
                headers=headers,
                timeout=15
            )
            resp.raise_for_status()
            data = resp.json()

            posts = data.get("data", {}).get("posts", {})
            edges = posts.get("edges", [])

            for edge in edges:
                node = edge["node"]
                makers = node.get("makers", [])

                # Check if any maker mentions India in headline
                india_maker = any(
                    "india" in (m.get("headline") or "").lower()
                    or any(city in (m.get("headline") or "").lower()
                           for city in ["bengaluru", "bangalore", "mumbai", "delhi", "hyderabad", "pune", "chennai"])
                    for m in makers
                )

                if india_maker:
                    results.append({
                        "name": node["name"],
                        "tagline": node["tagline"],
                        "ph_url": node["url"],
                        "votes": node["votesCount"],
                        "created": node["createdAt"],
                        "makers": [
                            {"name": m["name"], "headline": m.get("headline")}
                            for m in makers
                        ],
                        "topics": [
                            e["node"]["name"]
                            for e in node.get("topics", {}).get("edges", [])
                        ],
                        "source": "producthunt_api"
                    })

            page_info = posts.get("pageInfo", {})
            if page_info.get("hasNextPage"):
                cursor = page_info["endCursor"]
            else:
                break

            pages += 1
            time.sleep(1)

        except Exception as e:
            print(f"  [!] API error: {e}")
            break

    return results


def run(ph_token: str = None):
    """Main entry point."""
    print("\n=== Product Hunt Scraper ===\n")

    if ph_token:
        print("Using Product Hunt API...")
        results = search_producthunt_api(ph_token)
    else:
        print("No PH token - falling back to Google dorking...")
        results = search_producthunt_google()

    print(f"\nTotal Product Hunt results: {len(results)}")

    output_path = Path(__file__).parent.parent / "data" / "producthunt_raw.json"
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Saved to {output_path}")

    return results


if __name__ == "__main__":
    import sys
    token = sys.argv[1] if len(sys.argv) > 1 else None
    run(token)
