"""
Deal Flow Pipeline - Reddit Scraper
Finds early-stage Indian founders sharing progress on:
  r/IndiaStartups, r/startups, r/SomethingIMade, r/entrepreneur

Uses Google dorking (no Reddit API key required).
"""

import json
import re
from pathlib import Path

from utils import web_search as google_search  # DDG-primary, Google fallback


# Reddit restricted search-engine crawling in mid-2023.  site:reddit.com/r/...
# returns almost nothing from GH Actions.  We strip the site: operator at
# runtime and use the subreddit name as a plain keyword instead, which still
# biases results toward Reddit posts while avoiding the block.
REDDIT_QUERIES = [
    # r/IndiaStartups - highest signal for Indian founders
    ('site:reddit.com/r/IndiaStartups "building" OR "launched" OR "raised" 2024 2025', "reddit:IndiaStartups"),
    ('site:reddit.com/r/IndiaStartups "pre-seed" OR "seed" OR "angel" India startup 2024 2025', "reddit:IndiaStartups"),
    ('site:reddit.com/r/IndiaStartups "Show" startup India AI health consumer 2024', "reddit:IndiaStartups"),
    ('site:reddit.com/r/IndiaStartups founder "I\'m building" OR "we launched" 2025', "reddit:IndiaStartups"),

    # r/SomethingIMade - Show HN equivalent, India-tagged
    ('site:reddit.com/r/SomethingIMade "India" startup AI health consumer 2024 2025', "reddit:SomethingIMade"),
    ('site:reddit.com/r/SomethingIMade "India" founder "built" "launched" 2025', "reddit:SomethingIMade"),

    # r/startups - Indian founders post here too
    ('site:reddit.com/r/startups "India" "building" OR "launched" AI health consumer 2024 2025', "reddit:startups"),
    ('site:reddit.com/r/startups "India" "pre-seed" OR "seed" startup 2024 2025', "reddit:startups"),
    ('site:reddit.com/r/startups "India" founder "quit" OR "left" "building" 2024', "reddit:startups"),

    # r/entrepreneur - Indian founder signals
    ('site:reddit.com/r/entrepreneur "India" "startup" founder building launched 2024 2025', "reddit:entrepreneur"),
    ('site:reddit.com/r/entrepreneur "India" "AI" OR "healthtech" OR "fintech" startup founder 2025', "reddit:entrepreneur"),
]

# Extracts subreddit name from site:reddit.com/r/<name>
_SUBREDDIT_RE = re.compile(r'site:reddit\.com/r/(\w+)', re.IGNORECASE)
# Matches any reddit.com/r/.../comments/... URL
_REDDIT_POST_RE = re.compile(r'reddit\.com/r/\w+/comments/')


def is_reddit_post(url: str) -> bool:
    """Check if URL is a Reddit post (not a subreddit homepage or user page)."""
    return bool(_REDDIT_POST_RE.search(url))


def run():
    """Main entry point."""
    print("\n=== Reddit Scraper (Google Dorking) ===\n")

    all_results = []
    seen_urls: set[str] = set()

    for query, source_tag in REDDIT_QUERIES:
        # Strip site: operator; keep subreddit name as keyword for bias
        m = _SUBREDDIT_RE.search(query)
        subreddit = m.group(1) if m else "reddit"
        safe_q = _SUBREDDIT_RE.sub('', query).strip()
        if subreddit.lower() not in safe_q.lower():
            safe_q += f' r/{subreddit}'

        print(f"  Searching [{source_tag}]: {safe_q[:70]}...")
        hits = google_search(safe_q, 10)
        for h in hits:
            url     = h.get("url", "")
            snippet = h.get("snippet", "")
            title   = h.get("title", "")

            # 1. Result URL is a Reddit post
            if is_reddit_post(url):
                reddit_url = url.split("?")[0]
            else:
                # 2. Reddit post URL embedded in snippet or title
                m2 = _REDDIT_POST_RE.search(snippet + " " + title)
                if not m2:
                    continue
                # Extract the full URL from snippet (best effort)
                full_m = re.search(r'https?://(?:www\.)?reddit\.com/r/\w+/comments/\S+', snippet + " " + title)
                reddit_url = full_m.group(0).rstrip('.,)') if full_m else None

            if reddit_url:
                url_clean = reddit_url.lower()
                if url_clean not in seen_urls:
                    seen_urls.add(url_clean)
                    all_results.append({
                        "url":         reddit_url,
                        "title":       title,
                        "snippet":     snippet,
                        "source":      source_tag,
                        "source_type": source_tag,
                    })

    print(f"\nTotal unique Reddit posts found: {len(all_results)}")

    output_path = Path(__file__).parent.parent / "data" / "reddit_raw.json"
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"Saved to {output_path}")

    return all_results


if __name__ == "__main__":
    run()
