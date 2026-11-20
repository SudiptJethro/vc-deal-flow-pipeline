"""
Deal Flow Pipeline - Orchestrator
Runs all scrapers, enriches results, deduplicates, and outputs final JSON.

Usage:
    python run_all.py                  # Run all scrapers
    python run_all.py --skip-scrape    # Only run enricher on existing raw data
    python run_all.py --ph-token XXX   # Include Product Hunt API scraping

Requirements:
    pip install requests beautifulsoup4
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Add scripts dir to path
sys.path.insert(0, str(Path(__file__).parent))

from config import EXCLUDED_STARTUPS


def upload_to_d1(
    startups: list[dict],
    account_id: str,
    database_id: str,
    api_token: str,
    batch_size: int = 50,
) -> None:
    """
    Push enriched startups to Cloudflare D1 via the REST API batch endpoint.
    Sends up to `batch_size` statements per HTTP request instead of one per row,
    reducing 600 sequential calls to ~12.

    Batch API docs: https://developers.cloudflare.com/api/operations/cloudflare-d1-batch-database
    """
    import urllib.request as urlreq

    query_url = (
        f"https://api.cloudflare.com/client/v4/accounts/{account_id}"
        f"/d1/database/{database_id}/query"
    )
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }

    INSERT_SQL = """
        INSERT INTO startups
          (founder_name, startup_name, linkedin_url, website, sector,
           one_liner, tier, tier_rationale, source, founded_year, city, funding_stage,
           is_new)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(founder_name, startup_name) DO UPDATE SET
          linkedin_url   = COALESCE(excluded.linkedin_url,   startups.linkedin_url),
          website        = COALESCE(excluded.website,        startups.website),
          sector         = excluded.sector,
          one_liner      = excluded.one_liner,
          tier           = excluded.tier,
          tier_rationale = excluded.tier_rationale,
          source         = excluded.source,
          founded_year   = excluded.founded_year,
          city           = COALESCE(excluded.city,           startups.city),
          funding_stage  = COALESCE(excluded.funding_stage,  startups.funding_stage),
          is_new         = 0,
          updated_at     = datetime('now')
    """.strip()

    def _make_params(s: dict) -> list:
        return [
            s.get("founder_name", "Unknown"),
            s.get("startup_name", "Unknown"),
            s.get("linkedin_url"),
            s.get("website"),
            s.get("sector", "Consumer Tech"),
            (s.get("one_liner") or "")[:120],
            s.get("tier", 3),
            (s.get("tier_rationale") or "")[:100],
            s.get("source", "Pipeline"),
            s.get("founded_year", 2024),
            s.get("city"),
            s.get("funding_stage"),
            1 if s.get("is_new") else 0,
        ]

    total = 0
    errors = 0
    logged_errors = 0
    batches = [startups[i:i + batch_size] for i in range(0, len(startups), batch_size)]

    for batch_num, batch in enumerate(batches, 1):
        batch_ok = 0
        batch_errors = 0
        for s in batch:
            body = json.dumps({"sql": INSERT_SQL, "params": _make_params(s)}).encode()
            req = urlreq.Request(query_url, data=body, headers=headers, method="POST")
            try:
                with urlreq.urlopen(req, timeout=30) as r:
                    result = json.loads(r.read())
                    if result.get("success"):
                        batch_ok += 1
                    else:
                        batch_errors += 1
                        if logged_errors < 3:
                            print(f"  [!] Row error: {result.get('errors')}")
                            logged_errors += 1
            except Exception as e:
                batch_errors += 1
                if logged_errors < 3:
                    print(f"  [!] Row upload failed: {e}")
                    logged_errors += 1
        total += batch_ok
        errors += batch_errors
        print(f"  Batch {batch_num}/{len(batches)} - {total} upserted, {errors} errors")

    print(f"  D1 upload complete: {total} upserted, {errors} errors out of {len(startups)}")


def main():
    parser = argparse.ArgumentParser(description="Deal Flow Pipeline Orchestrator")
    parser.add_argument("--skip-scrape", action="store_true", help="Skip scraping, only enrich")
    parser.add_argument("--ph-token", type=str, default=None, help="Product Hunt API token")
    parser.add_argument("--cf-account-id",  type=str, default=None, help="Cloudflare Account ID")
    parser.add_argument("--cf-api-token",   type=str, default=None, help="Cloudflare API Token (D1 Edit permission)")
    parser.add_argument("--cf-db-id",       type=str, default=os.environ.get("CF_D1_DATABASE_ID"),
                        help="Cloudflare D1 database ID (or set CF_D1_DATABASE_ID)")
    args = parser.parse_args()

    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)

    if not args.skip_scrape:
        print("=" * 60)
        print("  DEAL FLOW PIPELINE - Full Run")
        print("=" * 60)

        # 1. LinkedIn scraping
        print("\n[1/10] LinkedIn Scraper...")
        try:
            from linkedin_scraper import run as run_linkedin
            run_linkedin()
        except Exception as e:
            print(f"  [!] LinkedIn scraper failed: {e}")

        # 2. Twitter scraping
        print("\n[2/10] Twitter Scraper...")
        try:
            from twitter_scraper import run as run_twitter
            run_twitter()
        except Exception as e:
            print(f"  [!] Twitter scraper failed: {e}")

        # 3. Product Hunt scraping
        print("\n[3/10] Product Hunt Scraper...")
        try:
            from producthunt_scraper import run as run_ph
            run_ph(args.ph_token)
        except Exception as e:
            print(f"  [!] Product Hunt scraper failed: {e}")

        # 4. Accelerator scraping (YC, Antler, SURGE, 100X, Techstars, GSF, 500, P&P,
        #    IIM NASSCOM, Rocket, 9Unicorns, Axilor, Venture Catalysts,
        #    Better Capital, First Cheque, Titan Capital, Kstart, Blume,
        #    T-Hub, CIIE.CO, NSRCEL, SINE, FITT, Kerala SM, AIM, TiE, F6S, DPIIT,
        #    Elevation, Fireside, India Quotient, Prime VP, Fundamentum,
        #    DSG Consumer, Arali, Pravega, All In Capital)
        print("\n[4/10] Accelerator Scraper...")
        try:
            from accelerator_scraper import run as run_accel
            run_accel()
        except Exception as e:
            print(f"  [!] Accelerator scraper failed: {e}")

        # 5. Reddit scraping (r/IndiaStartups, r/startups, r/SomethingIMade, r/entrepreneur)
        print("\n[5/10] Reddit Scraper...")
        try:
            from reddit_scraper import run as run_reddit
            run_reddit()
        except Exception as e:
            print(f"  [!] Reddit scraper failed: {e}")

        # 6. Indian Directory + High-Signal Sources
        #    (Inc42, YourStory, Wellfound, Nasscom, HN, VC portfolios,
        #     AngelList, Google News, SEBI, CB Insights, Gust)
        print("\n[6/10] Directory & High-Signal Source Scraper...")
        try:
            from directory_scraper import run as run_directory
            run_directory()
        except Exception as e:
            print(f"  [!] Directory scraper failed: {e}")

        # 7. Google News / Media funding announcements
        #    (Inc42, YourStory, ET, Mint, Entrackr, VCCircle, TechCrunch India,
        #     Forbes India, Business Today, Financial Express, RestOfWorld, NDTV)
        print("\n[7/10] Google News / Media Scraper...")
        try:
            from news_scraper import run as run_news
            run_news()
        except Exception as e:
            print(f"  [!] News scraper failed: {e}")

        # 8. Crunchbase (Google dorking on crunchbase.com/organization)
        print("\n[8/10] Crunchbase Scraper...")
        try:
            from crunchbase_scraper import run as run_crunchbase
            run_crunchbase()
        except Exception as e:
            print(f"  [!] Crunchbase scraper failed: {e}")

        # 9. Tracxn (Google dorking on tracxn.com)
        print("\n[9/10] Tracxn Scraper...")
        try:
            from trackxn_scraper import run as run_tracxn
            run_tracxn()
        except Exception as e:
            print(f"  [!] Tracxn scraper failed: {e}")

        # 10. Hacker News - Show HN / Ask HN / stories from India founders
        print("\n[10/10] Hacker News Algolia Scraper...")
        try:
            from hn_scraper import run as run_hn
            run_hn()
        except Exception as e:
            print(f"  [!] HN scraper failed: {e}")

    # Enrich all raw data (runs regardless of --skip-scrape)
    print("\n[Enricher] Enriching and merging all data...")
    try:
        from enricher import run as run_enricher
        final = run_enricher()
    except Exception as e:
        print(f"  [!] Enricher failed: {e}")
        final = []

    # Upload directly to Cloudflare D1 via REST API (bypasses Worker/WAF)
    if final and args.cf_account_id and args.cf_api_token and args.cf_db_id:
        print(f"\n[Upload] Pushing {len(final)} startups directly to Cloudflare D1...")
        upload_to_d1(final, args.cf_account_id, args.cf_db_id, args.cf_api_token)

    # Copy to dashboard
    dashboard_data = data_dir.parent / "dashboard" / "data.js"
    if final and dashboard_data.parent.exists():
        js_content = "const STARTUPS_DATA = " + json.dumps(final, indent=2, ensure_ascii=False) + ";\n"
        with open(dashboard_data, "w", encoding="utf-8") as f:
            f.write(js_content)
        print(f"\nUpdated dashboard data.js with {len(final)} startups")

    # Summary
    print("\n" + "=" * 60)
    print(f"  PIPELINE COMPLETE")
    print(f"  Total startups: {len(final)}")
    if final:
        sectors = {}
        tiers = {}
        for s in final:
            sectors[s.get("sector", "?")] = sectors.get(s.get("sector", "?"), 0) + 1
            tiers[s.get("tier", "?")] = tiers.get(s.get("tier", "?"), 0) + 1
        print(f"  By sector: {sectors}")
        print(f"  By tier: {tiers}")
        linkedin_count = sum(1 for s in final if s.get("linkedin_url"))
        print(f"  With LinkedIn: {linkedin_count}/{len(final)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
