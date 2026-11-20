"""
Deal Flow Pipeline - Indian Directory & High-Signal Source Scraper

Covers all sources from the user's directory list:
  Indian Startup Directories:
    Wellfound (AngelList India), Inc42, YourStory, Startup India Hub,
    Nasscom Startup Members, IAMAI Members, IIM NASSCOM Mentorship Portal

  Global High-Signal Sources:
    Hacker News (Show HN), AngelList Syndicates, Gust/SeedInvest,
    CB Insights, PitchBook (free pages), Rolling Funds (a16z)

  VC Portfolio Pages (India-focused):
    Sequoia/Peak XV, Lightspeed India, Matrix Partners India,
    Accel India, Blume Ventures, Nexus VP, Kalaari Capital,
    Stellaris Venture Partners, Chiratae, 3one4 Capital

  Data Enrichment Sources:
    Google News funding rounds, SEBI filings (Dhruva / BSE),
    Economic Times, Mint, Business Standard

Uses Google dorking (no API keys required).
"""

import json
from pathlib import Path

from utils import web_search as google_search  # DDG-primary, Google fallback


# ── Source query groups ────────────────────────────────────────────────────────

INC42_QUERIES = [
    ('site:inc42.com "startup" India "pre-seed" OR "seed" AI health consumer 2024', "inc42:funding"),
    ('site:inc42.com "raises" startup India AI 2024 2025', "inc42:funding"),
    ('site:inc42.com "raises" startup India healthtech consumer 2025', "inc42:funding"),
    ('site:inc42.com "launches" startup India founder 2024 2025', "inc42:launch"),
    ('site:inc42.com startup India "Series A" AI health consumer 2024 2025', "inc42:series_a"),
]

YOURSTORY_QUERIES = [
    ('site:yourstory.com startup India "pre-seed" OR "seed" AI health consumer 2024', "yourstory:funding"),
    ('site:yourstory.com "raises" startup India 2024 2025', "yourstory:funding"),
    ('site:yourstory.com "launches" startup founder India AI health 2025', "yourstory:launch"),
    ('site:yourstory.com startup India founder "built" OR "building" 2024 2025', "yourstory:founder"),
]

WELLFOUND_QUERIES = [
    ('site:wellfound.com/company India startup "pre-seed" AI health consumer 2024 2025', "wellfound:company"),
    ('site:wellfound.com/company India startup seed "looking for" AI health 2024', "wellfound:company"),
    ('site:angel.co/company India startup pre-seed seed AI health consumer 2024 2025', "wellfound:angellist"),
]

STARTUP_INDIA_QUERIES = [
    ('site:startupindia.gov.in startup "recognized" India AI health consumer 2024 2025', "startup_india:registry"),
    ('"startup india" "recognized" startup India AI health consumer 2024 2025', "startup_india:recognition"),
    ('site:nasscom.in startup member India AI health consumer 2024 2025', "nasscom:member"),
    ('"nasscom" "startup" India "AI" OR "healthtech" OR "consumer" 2024 2025 founder', "nasscom:directory"),
    ('"IAMAI" India startup member AI health consumer fintech 2024 2025', "nasscom:iamai"),
    ('"IIM NASSCOM" startup mentorship India AI health 2024 2025', "nasscom:iim_nasscom"),
]

HACKERNEWS_QUERIES = [
    ('site:news.ycombinator.com "Show HN" India startup AI 2024 2025', "hackernews:show_hn"),
    ('site:news.ycombinator.com "Show HN" India health consumer 2024 2025', "hackernews:show_hn"),
    ('site:news.ycombinator.com "Ask HN" India startup founder 2024 2025', "hackernews:ask_hn"),
    ('site:news.ycombinator.com India "launched" startup founder AI health 2024', "hackernews:launch"),
]

VC_PORTFOLIO_QUERIES = [
    # Peak XV / Sequoia India
    ('site:peakxv.com portfolio startup India 2024 2025', "vc_portfolio:peak_xv"),
    ('"Peak XV" portfolio India startup AI health consumer 2024 2025', "vc_portfolio:peak_xv"),
    # Lightspeed India
    ('site:lsvp.com portfolio India startup 2024 2025', "vc_portfolio:lightspeed"),
    ('"Lightspeed India" portfolio startup AI health consumer 2024 2025', "vc_portfolio:lightspeed"),
    # Matrix Partners India
    ('site:matrixpartners.in portfolio startup 2024 2025', "vc_portfolio:matrix"),
    ('"Matrix Partners India" portfolio startup AI health consumer 2024 2025', "vc_portfolio:matrix"),
    # Accel India
    ('site:accel.com/portfolio India startup 2024 2025', "vc_portfolio:accel"),
    ('"Accel India" portfolio startup AI health consumer 2024 2025', "vc_portfolio:accel"),
    # Blume Ventures
    ('site:blume.vc portfolio startup India 2024 2025', "vc_portfolio:blume"),
    # Nexus VP
    ('site:nexusvp.com portfolio India startup 2024 2025', "vc_portfolio:nexus"),
    # Kalaari Capital
    ('site:kalaari.com portfolio startup India 2024 2025', "vc_portfolio:kalaari"),
    # Stellaris VP
    ('site:stellaris.in portfolio startup India 2024 2025', "vc_portfolio:stellaris"),
    # Chiratae (formerly IDG Ventures India)
    ('site:chiratae.com portfolio startup India 2024 2025', "vc_portfolio:chiratae"),
    # 3one4 Capital
    ('site:3one4.com portfolio startup India 2024 2025', "vc_portfolio:3one4"),
    # AngelList India syndicates
    ('site:angel.co/syndicates India startup "deal" AI health consumer 2024 2025', "angellist:syndicate"),
]

ROLLING_FUND_QUERIES = [
    ('"a16z" rolling fund OR "Andreessen Horowitz" India startup portfolio 2024 2025', "vc_portfolio:a16z"),
    ('"Gust" India startup pre-seed seed 2024 2025', "gust:funding"),
    ('"SeedInvest" India startup pre-seed 2024 2025', "gust:seedinvest"),
]

GOOGLE_NEWS_QUERIES = [
    # Economic Times / Mint / Business Standard - funding rounds
    ('site:economictimes.com "raises" OR "secures" startup India AI health consumer 2024 2025', "google_news:et"),
    ('site:livemint.com "raises" startup India AI health consumer pre-seed seed 2024 2025', "google_news:mint"),
    ('site:business-standard.com "startup" India "raises" AI health consumer 2024 2025', "google_news:bs"),
    # Google News aggregate
    ('"India" startup "raises" "pre-seed" AI health consumer 2024 2025', "google_news:general"),
    ('"India" startup "raises" "seed" AI health consumer 2024 2025', "google_news:general"),
    ('"India" startup founded "AI" OR "healthtech" "2025" pre-seed seed', "google_news:general"),
]

SEBI_QUERIES = [
    ('site:bseindia.com startup India 2024 2025 "incorporated"', "sebi:bse"),
    ('"SEBI" "startup" India "new listing" OR "SME IPO" AI health 2024 2025', "sebi:filing"),
    ('"MCA" "incorporated" India startup AI health consumer 2024 2025', "sebi:mca"),
]

CB_INSIGHTS_QUERIES = [
    ('site:cbinsights.com India startup AI health consumer 2024 2025', "vc_portfolio:cb_insights"),
    ('"CB Insights" India startup AI health consumer "pre-seed" OR "seed" 2024 2025', "vc_portfolio:cb_insights"),
]


def scrape_group(queries: list[tuple[str, str]], group_name: str, seen_urls: set) -> list[dict]:
    """Run a group of queries and return deduplicated results."""
    results = []
    print(f"\n  [{group_name}]")
    for query, source_tag in queries:
        print(f"    Searching: {query[:75]}...")
        hits = google_search(query, 10)
        for h in hits:
            url_clean = h["url"].split("?")[0].lower()
            if url_clean and url_clean not in seen_urls:
                seen_urls.add(url_clean)
                results.append({
                    "url": h["url"].split("?")[0],
                    "title": h["title"],
                    "snippet": h["snippet"],
                    "source": source_tag,
                    "source_type": source_tag,
                })
    print(f"    → {len(results)} new results from {group_name}")
    return results


def run():
    """Main entry point."""
    print("\n=== Indian Directory & High-Signal Source Scraper ===\n")
    print("Sources: Inc42, YourStory, Wellfound, Startup India, Nasscom, IAMAI,")
    print("         Hacker News, VC Portfolios, AngelList, Rolling Funds,")
    print("         Google News, SEBI, CB Insights\n")

    all_results = []
    seen_urls: set = set()

    groups = [
        (INC42_QUERIES,        "Inc42"),
        (YOURSTORY_QUERIES,    "YourStory"),
        (WELLFOUND_QUERIES,    "Wellfound/AngelList"),
        (STARTUP_INDIA_QUERIES,"Startup India / Nasscom / IAMAI"),
        (HACKERNEWS_QUERIES,   "Hacker News"),
        (VC_PORTFOLIO_QUERIES, "VC Portfolio Pages"),
        (ROLLING_FUND_QUERIES, "Rolling Funds / Gust / SeedInvest"),
        (GOOGLE_NEWS_QUERIES,  "Google News / ET / Mint"),
        (SEBI_QUERIES,         "SEBI / MCA Filings"),
        (CB_INSIGHTS_QUERIES,  "CB Insights"),
    ]

    for queries, name in groups:
        batch = scrape_group(queries, name, seen_urls)
        all_results.extend(batch)

    print(f"\nTotal unique directory results: {len(all_results)}")

    output_path = Path(__file__).parent.parent / "data" / "directory_raw.json"
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"Saved to {output_path}")

    return all_results


if __name__ == "__main__":
    run()
