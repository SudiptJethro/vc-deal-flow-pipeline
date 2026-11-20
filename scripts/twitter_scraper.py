"""
Deal Flow Pipeline - Twitter/X Scraper (via Google Dorking)
Finds founders who posted about building startups on Twitter/X.
No Twitter API needed - uses Google search.
"""

import json
import re
from pathlib import Path

from utils import web_search as google_search  # DDG-primary, Google fallback


# Matches twitter.com/<user>/status/... or x.com/<user>/status/...
_TX_URL_RE = re.compile(r'(?:twitter|x)\.com/(\w+)(?:/status/\d+)?')


def search_twitter_founders() -> list[dict]:
    """Search Twitter/X for Indian founders announcing new startups.

    site:twitter.com / site:x.com are stripped at runtime - Twitter/X
    de-indexes most posts, and DDG blocks GH Actions IPs for site: queries.
    'twitter OR x.com' is appended to bias results toward tweets/profiles.
    Twitter/X URLs are captured from both the result URL and snippet text.
    """
    queries = [
        'site:twitter.com "building" "startup" "India" "AI" 2024',
        'site:twitter.com "building" "startup" "India" "AI" 2025',
        'site:twitter.com "building" "startup" "India" "consumer" 2024',
        'site:twitter.com "building" "startup" "India" "consumer" 2025',
        'site:twitter.com "building" "startup" "India" "health" 2024',
        'site:twitter.com "building" "startup" "India" "health" 2025',
        'site:x.com "I\'m building" "India" "AI" founder 2024',
        'site:x.com "I\'m building" "India" "AI" founder 2025',
        'site:x.com "quit my job" "building" "India" startup 2024',
        'site:x.com "quit my job" "building" "India" startup 2025',
        'site:twitter.com "launched" "India" "startup" "AI" 2024',
        'site:twitter.com "launched" "India" "startup" "AI" 2025',
        'site:twitter.com "stealth" "founder" "India" "building" 2024',
        'site:twitter.com "stealth" "founder" "India" "building" 2025',
        'site:x.com "ex-Swiggy" OR "ex-Razorpay" OR "ex-CRED" founder building',
        'site:x.com "ex-Flipkart" OR "ex-Meesho" OR "ex-PhonePe" founder building',
        'site:x.com "India" "founder" "pre-seed" OR "seed" "AI" 2025',
        'site:x.com "India" "founder" "healthtech" OR "femtech" building 2025',
        'site:x.com "India" "YC" OR "Antler" founder startup 2024 2025',
        'site:x.com "India" "genai" OR "LLM" startup founder 2025',
    ]

    results = []
    seen: set[str] = set()

    for q in queries:
        # Strip site: operator; append bias keyword
        safe_q = re.sub(r'\bsite:(?:twitter|x)\.com\s*', '', q).strip()
        if 'twitter' not in safe_q.lower() and 'x.com' not in safe_q.lower():
            safe_q += ' twitter OR x.com'

        print(f"  Searching: {safe_q[:60]}...")
        hits = google_search(safe_q)
        for h in hits:
            url     = h.get("url", "")
            snippet = h.get("snippet", "")
            title   = h.get("title", "")

            # 1. Result URL is a tweet or profile
            if "twitter.com/" in url or "x.com/" in url:
                tx_url = url.split("?")[0]
            else:
                # 2. Twitter/X URL embedded in snippet or title
                m = _TX_URL_RE.search(snippet + " " + title)
                tx_url = (
                    f"https://twitter.com/{m.group(1)}" if m else None
                )

            if tx_url:
                key = tx_url.lower()
                if key not in seen:
                    seen.add(key)
                    results.append({
                        "twitter_url":  tx_url,
                        "title":        title,
                        "snippet":      snippet,
                        "query_source": "twitter_search",
                    })

    return results


def run():
    """Main entry point."""
    print("\n=== Twitter/X Scraper (Google Dorking) ===\n")

    founders = search_twitter_founders()
    print(f"\nTotal unique Twitter posts found: {len(founders)}")

    output_path = Path(__file__).parent.parent / "data" / "twitter_raw.json"
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(founders, f, indent=2, ensure_ascii=False)
    print(f"Saved to {output_path}")

    return founders


if __name__ == "__main__":
    run()
