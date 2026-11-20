"""
Deal Flow Pipeline - Accelerator Portfolio Scraper
Scrapes public portfolio pages of YC, Antler India, SURGE, 100X.VC.
"""

import json
from pathlib import Path

from config import ACCELERATOR_URLS, SECTOR_KEYWORDS
from utils import web_search as google_search, jina_read, jina_extract_startups, fetch_page


def scrape_yc_india() -> list[dict]:
    """Search for YC India batch companies (2024-2025)."""
    print("  Scraping YC India startups...")
    queries = [
        "Y Combinator India startups 2024 batch list",
        "Y Combinator India startups 2025 batch consumer AI health",
        "YC W24 S24 India founders startups",
        "YC W25 S25 India founders startups",
        "site:ycombinator.com/companies India consumer AI health 2024",
    ]

    results = []
    for q in queries:
        hits = google_search(q, 10)
        for h in hits:
            results.append({**h, "accelerator": "YC"})
    return results


def scrape_antler_india() -> list[dict]:
    """Search for Antler India portfolio companies."""
    print("  Scraping Antler India portfolio...")
    queries = [
        "Antler India portfolio 2024 startups founders list",
        "Antler India cohort 2024 consumer AI healthtech",
        "site:antler.co India portfolio startups",
        "Antler India invested startups 2024 2025",
    ]

    results = []
    for q in queries:
        hits = google_search(q, 10)
        for h in hits:
            results.append({**h, "accelerator": "Antler India"})
    return results


def scrape_surge() -> list[dict]:
    """Search for SURGE (Peak XV/Sequoia) accelerator companies."""
    print("  Scraping SURGE portfolio...")
    queries = [
        "SURGE accelerator India portfolio 2024 startups",
        "Peak XV SURGE cohort 2024 2025 India startups",
        "Sequoia SURGE India startups consumer AI health",
        "site:peakxv.com surge startups India",
    ]

    results = []
    for q in queries:
        hits = google_search(q, 10)
        for h in hits:
            results.append({**h, "accelerator": "SURGE"})
    return results


def scrape_100x_vc() -> list[dict]:
    """Search for 100X.VC portfolio companies."""
    print("  Scraping 100X.VC portfolio...")
    queries = [
        "100X.VC portfolio 2024 India startups consumer AI health",
        "100X.VC batch 2024 startups list founders",
    ]

    results = []
    for q in queries:
        hits = google_search(q, 10)
        for h in hits:
            results.append({**h, "accelerator": "100X.VC"})
    return results


def scrape_techstars_india() -> list[dict]:
    """Search for Techstars India portfolio companies."""
    print("  Scraping Techstars India portfolio...")
    queries = [
        "Techstars India portfolio 2024 2025 startups founders list",
        "site:techstars.com portfolio India startup AI health consumer 2024",
        "Techstars Mumbai OR Bangalore OR Delhi India batch 2024 2025 startups",
    ]
    results = []
    for q in queries:
        hits = google_search(q, 10)
        for h in hits:
            results.append({**h, "accelerator": "Techstars India"})
    return results


def scrape_gsf_india() -> list[dict]:
    """Search for GSF (Global Super Founders) India portfolio."""
    print("  Scraping GSF India portfolio...")
    queries = [
        "GSF India accelerator portfolio 2024 2025 startups founders",
        "site:gsf.in portfolio startup India AI health consumer 2024 2025",
        "Global Super Founders India cohort 2024 startups list",
    ]
    results = []
    for q in queries:
        hits = google_search(q, 10)
        for h in hits:
            results.append({**h, "accelerator": "GSF India"})
    return results


def scrape_500_startups_india() -> list[dict]:
    """Search for 500 Startups India portfolio."""
    print("  Scraping 500 Startups India portfolio...")
    queries = [
        "500 Startups India portfolio 2024 2025 startup founders list",
        "site:500.co portfolio India startup AI health consumer 2024",
        "500 Global India cohort batch 2024 2025 startups",
    ]
    results = []
    for q in queries:
        hits = google_search(q, 10)
        for h in hits:
            results.append({**h, "accelerator": "500 Startups India"})
    return results


def scrape_plug_and_play_india() -> list[dict]:
    """Search for Plug and Play India accelerator portfolio."""
    print("  Scraping Plug and Play India portfolio...")
    queries = [
        "Plug and Play India accelerator portfolio 2024 2025 startups",
        "site:plugandplaytechcenter.com India startup 2024 2025",
        "Plug and Play India cohort batch startup AI health fintech 2024 2025",
    ]
    results = []
    for q in queries:
        hits = google_search(q, 10)
        for h in hits:
            results.append({**h, "accelerator": "Plug and Play India"})
    return results


def scrape_iim_nasscom() -> list[dict]:
    """Search for IIM NASSCOM mentorship portal startups."""
    print("  Scraping IIM NASSCOM Mentorship Portal startups...")
    queries = [
        "IIM NASSCOM mentorship portal India startup 2024 2025 list",
        '"IIM NASSCOM" startup India AI health consumer founder 2024 2025',
        "NASSCOM IIM startup mentorship India cohort 2024 batch startups",
    ]
    results = []
    for q in queries:
        hits = google_search(q, 10)
        for h in hits:
            results.append({**h, "accelerator": "IIM NASSCOM Mentorship"})
    return results


def scrape_rocket_internet() -> list[dict]:
    """Search for Rocket Internet alumni founding new startups in India."""
    print("  Scraping Rocket Internet India alumni startups...")
    queries = [
        '"Rocket Internet" India alumni founder startup 2024 2025',
        '"ex-Rocket Internet" India startup founder building 2024 2025',
    ]
    results = []
    for q in queries:
        hits = google_search(q, 10)
        for h in hits:
            results.append({**h, "accelerator": "Rocket Internet Alumni"})
    return results


def scrape_9unicorns() -> list[dict]:
    """Search for 9Unicorns accelerator portfolio (India-focused, pre-seed)."""
    print("  Scraping 9Unicorns portfolio...")
    queries = [
        "9Unicorns accelerator India portfolio 2024 2025 startups founders list",
        "site:9unicorns.com portfolio startup India AI health consumer 2024 2025",
        "9Unicorns cohort batch India startup founder 2024 2025",
        '"9Unicorns" India startup founder "pre-seed" OR "seed" 2024 2025',
    ]
    results = []
    for q in queries:
        hits = google_search(q, 10)
        for h in hits:
            results.append({**h, "accelerator": "9Unicorns"})
    return results


def scrape_axilor() -> list[dict]:
    """Search for Axilor Ventures portfolio (Narayana Murthy-backed, Bengaluru)."""
    print("  Scraping Axilor Ventures portfolio...")
    queries = [
        "Axilor Ventures portfolio India 2024 2025 startups founders list",
        "site:axilor.com portfolio startup India 2024 2025",
        "Axilor India accelerator cohort startup 2024 2025 consumer AI health",
        '"Axilor" India startup founder "pre-seed" OR "seed" 2024 2025',
    ]
    results = []
    for q in queries:
        hits = google_search(q, 10)
        for h in hits:
            results.append({**h, "accelerator": "Axilor Ventures"})
    return results


def scrape_venture_catalysts() -> list[dict]:
    """Search for Venture Catalysts (India's largest angel network)."""
    print("  Scraping Venture Catalysts portfolio...")
    queries = [
        "Venture Catalysts India portfolio 2024 2025 startups founders",
        "site:venturecatalysts.in portfolio startup India 2024 2025",
        '"Venture Catalysts" India startup founder funded 2024 2025',
        '"VCats" India startup funded consumer AI healthtech 2024 2025',
    ]
    results = []
    for q in queries:
        hits = google_search(q, 10)
        for h in hits:
            results.append({**h, "accelerator": "Venture Catalysts"})
    return results


def scrape_better_capital() -> list[dict]:
    """Search for Better Capital (India's top pre-seed fund)."""
    print("  Scraping Better Capital portfolio...")
    queries = [
        "Better Capital India portfolio 2024 2025 startups founders list",
        "site:bettercapital.us portfolio India startup 2024 2025",
        '"Better Capital" India startup founder "pre-seed" 2024 2025',
        '"Better Capital" India startup AI health consumer 2024 2025',
    ]
    results = []
    for q in queries:
        hits = google_search(q, 10)
        for h in hits:
            results.append({**h, "accelerator": "Better Capital"})
    return results


def scrape_first_cheque() -> list[dict]:
    """Search for First Cheque (India pre-seed community fund)."""
    print("  Scraping First Cheque portfolio...")
    queries = [
        "First Cheque India portfolio 2024 2025 startups founders list",
        "site:firstcheque.in portfolio startup India 2024 2025",
        '"First Cheque" India startup founder "pre-seed" OR "seed" 2024 2025',
        '"First Cheque" India startup AI health consumer fintech 2024 2025',
    ]
    results = []
    for q in queries:
        hits = google_search(q, 10)
        for h in hits:
            results.append({**h, "accelerator": "First Cheque"})
    return results


def scrape_titan_capital() -> list[dict]:
    """Search for Titan Capital (Snapdeal founders' fund, prolific India angel)."""
    print("  Scraping Titan Capital portfolio...")
    queries = [
        "Titan Capital India portfolio 2024 2025 startups founders list",
        "site:titan.capital portfolio startup India 2024 2025",
        '"Titan Capital" India startup founder funded 2024 2025',
        '"Titan Capital" India startup AI health consumer 2024 2025',
    ]
    results = []
    for q in queries:
        hits = google_search(q, 10)
        for h in hits:
            results.append({**h, "accelerator": "Titan Capital"})
    return results


def scrape_kstart() -> list[dict]:
    """Search for Kstart (Kalaari Capital's seed program)."""
    print("  Scraping Kstart / Kalaari Seed portfolio...")
    queries = [
        "Kstart Kalaari Capital seed India portfolio 2024 2025 startups",
        "site:kalaari.com portfolio India startup seed 2024 2025",
        '"Kstart" OR "Kalaari seed" India startup founder 2024 2025',
    ]
    results = []
    for q in queries:
        hits = google_search(q, 10)
        for h in hits:
            results.append({**h, "accelerator": "Kstart (Kalaari)"})
    return results


def scrape_blume_founders_fund() -> list[dict]:
    """Search for Blume Ventures seed / Blume Founders Fund."""
    print("  Scraping Blume Ventures portfolio...")
    queries = [
        "Blume Ventures portfolio India 2024 2025 startups founders list",
        "site:blume.vc portfolio India startup 2024 2025",
        '"Blume Ventures" India startup founder seed 2024 2025',
        '"Blume Founders Fund" India startup 2024 2025',
    ]
    results = []
    for q in queries:
        hits = google_search(q, 10)
        for h in hits:
            results.append({**h, "accelerator": "Blume Ventures"})
    return results


# ── India Incubators ──────────────────────────────────────────────────────────

def scrape_thub() -> list[dict]:
    """Search for T-Hub Hyderabad portfolio (India's largest startup incubator)."""
    print("  Scraping T-Hub Hyderabad portfolio...")
    queries = [
        "T-Hub Hyderabad portfolio 2024 2025 startups founders list",
        "site:t-hub.in startups portfolio India 2024 2025",
        '"T-Hub" Hyderabad startup AI health consumer fintech 2024 2025',
        '"T-Hub" India cohort incubated startup founder 2024 2025',
        'T-Hub accelerator India startup "consumer AI" OR "healthtech" 2024 2025',
    ]
    results = []
    for q in queries:
        hits = google_search(q, 10)
        for h in hits:
            results.append({**h, "accelerator": "T-Hub"})
    return results


def scrape_ciie() -> list[dict]:
    """Search for CIIE.CO (IIM Ahmedabad incubator) portfolio."""
    print("  Scraping CIIE.CO portfolio...")
    queries = [
        "CIIE.CO IIM Ahmedabad portfolio 2024 2025 startups founders",
        "site:ciie.co portfolio startup India 2024 2025",
        '"CIIE" "IIM Ahmedabad" startup incubated India 2024 2025',
        '"CIIE.CO" India startup AI health consumer 2024 2025',
        'CIIE IIM-A incubator India startup founder funded 2024 2025',
    ]
    results = []
    for q in queries:
        hits = google_search(q, 10)
        for h in hits:
            results.append({**h, "accelerator": "CIIE.CO (IIM-A)"})
    return results


def scrape_nsrcel() -> list[dict]:
    """Search for NSRCEL (IIM Bangalore) portfolio."""
    print("  Scraping NSRCEL (IIM Bangalore) portfolio...")
    queries = [
        "NSRCEL IIM Bangalore portfolio 2024 2025 startups founders list",
        "site:nsrcel.org portfolio startup India 2024 2025",
        '"NSRCEL" "IIM Bangalore" startup incubated 2024 2025',
        '"NSRCEL" India startup AI health consumer 2024 2025',
        'NSRCEL incubator India startup founder 2024 2025',
    ]
    results = []
    for q in queries:
        hits = google_search(q, 10)
        for h in hits:
            results.append({**h, "accelerator": "NSRCEL (IIM-B)"})
    return results


def scrape_sine_iitb() -> list[dict]:
    """Search for SINE (IIT Bombay incubator) portfolio."""
    print("  Scraping SINE IIT Bombay portfolio...")
    queries = [
        "SINE IIT Bombay incubator portfolio 2024 2025 startups founders",
        "site:sineiitb.org portfolio startup India 2024 2025",
        '"SINE" "IIT Bombay" startup incubated India 2024 2025',
        '"SINE IIT" India startup AI health consumer tech 2024 2025',
        'SINE IIT-B incubated startup India funded 2024 2025',
    ]
    results = []
    for q in queries:
        hits = google_search(q, 10)
        for h in hits:
            results.append({**h, "accelerator": "SINE (IIT-B)"})
    return results


def scrape_fitt_iitd() -> list[dict]:
    """Search for FITT (IIT Delhi) and IIT Delhi's incubation centre."""
    print("  Scraping FITT IIT Delhi portfolio...")
    queries = [
        "FITT IIT Delhi incubator portfolio 2024 2025 startups founders",
        "site:fitt.iitd.ac.in portfolio startup India 2024 2025",
        '"FITT" "IIT Delhi" startup incubated India 2024 2025',
        '"IIT Delhi incubated" startup India AI health consumer 2024 2025',
        'IIT Delhi startup incubation India funded 2024 2025',
    ]
    results = []
    for q in queries:
        hits = google_search(q, 10)
        for h in hits:
            results.append({**h, "accelerator": "FITT (IIT-D)"})
    return results


def scrape_kerala_startup_mission() -> list[dict]:
    """Search for Kerala Startup Mission (KSUM) portfolio."""
    print("  Scraping Kerala Startup Mission portfolio...")
    queries = [
        "Kerala Startup Mission KSUM portfolio 2024 2025 startups founders list",
        "site:startupmission.in portfolio startup Kerala 2024 2025",
        '"Kerala Startup Mission" startup incubated India 2024 2025',
        '"KSUM" Kerala startup AI health consumer 2024 2025',
        'Kerala startup ecosystem "seed" OR "funded" AI health consumer 2024 2025',
    ]
    results = []
    for q in queries:
        hits = google_search(q, 10)
        for h in hits:
            results.append({**h, "accelerator": "Kerala Startup Mission"})
    return results


def scrape_atal_innovation_mission() -> list[dict]:
    """Search for Atal Innovation Mission / Atal Incubation Centres portfolio."""
    print("  Scraping Atal Innovation Mission portfolio...")
    queries = [
        "Atal Incubation Centre AIC India startup 2024 2025 AI health consumer",
        '"Atal Innovation Mission" India startup incubated 2024 2025',
        '"AIC" "Atal" India startup funded AI health consumer 2024 2025',
        'site:aim.gov.in startups India 2024 2025',
        'Atal Incubation Centre India startup AI health fintech 2024 2025',
    ]
    results = []
    for q in queries:
        hits = google_search(q, 10)
        for h in hits:
            results.append({**h, "accelerator": "Atal Innovation Mission"})
    return results


def scrape_tie_india() -> list[dict]:
    """Search for TiE (The Indus Entrepreneurs) India accelerator/funded startups."""
    print("  Scraping TiE India portfolio...")
    queries = [
        "TiE India accelerator portfolio 2024 2025 startups founders",
        "TiE50 India winners 2024 2025 startup list",
        '"TiE" India startup funded "consumer AI" OR "healthtech" 2024 2025',
        '"TiE Delhi" OR "TiE Bangalore" OR "TiE Mumbai" startup 2024 2025',
        'TiE50 Global India AI health consumer winner 2024 2025',
    ]
    results = []
    for q in queries:
        hits = google_search(q, 10)
        for h in hits:
            results.append({**h, "accelerator": "TiE India"})
    return results


def scrape_f6s_india() -> list[dict]:
    """Search for F6S India accelerator/incubator programs."""
    print("  Scraping F6S India programs...")
    queries = [
        "site:f6s.com India startup program accelerator AI health consumer 2024 2025",
        "F6S India startup accelerator accepted cohort 2024 2025",
        '"F6S" India startup founder "consumer AI" OR "healthtech" 2024 2025',
        'F6S India accelerator batch startup AI health fintech 2024 2025',
    ]
    results = []
    for q in queries:
        hits = google_search(q, 10)
        for h in hits:
            results.append({**h, "accelerator": "F6S India"})
    return results


def scrape_startup_india_dpiit() -> list[dict]:
    """Search for DPIIT-recognized startups in target sectors."""
    print("  Scraping DPIIT Startup India recognized startups...")
    queries = [
        '"DPIIT recognized" startup India AI "consumer" OR "health" 2024 2025',
        '"Startup India recognized" "AI" India founder 2024 2025',
        '"DPIIT" "startup" India "consumer AI" OR "healthtech" funded 2024 2025',
        'site:startupindia.gov.in "AI" OR "healthtech" India startup 2024 2025',
        '"DPIIT certified" India startup founder "pre-seed" OR "seed" 2024 2025',
    ]
    results = []
    for q in queries:
        hits = google_search(q, 10)
        for h in hits:
            results.append({**h, "accelerator": "DPIIT / Startup India"})
    return results


# ── More VC Portfolios ────────────────────────────────────────────────────────

def scrape_elevation_capital() -> list[dict]:
    """Search for Elevation Capital (formerly SAIF Partners) portfolio."""
    print("  Scraping Elevation Capital portfolio...")
    queries = [
        "Elevation Capital portfolio India 2024 2025 startups founders list",
        "site:elevationcapital.com portfolio India startup 2024 2025",
        '"Elevation Capital" India startup funded "consumer AI" OR "healthtech" 2024 2025',
        '"SAIF Partners" OR "Elevation Capital" India startup seed 2024 2025',
    ]
    results = []
    for q in queries:
        hits = google_search(q, 10)
        for h in hits:
            results.append({**h, "accelerator": "Elevation Capital"})
    return results


def scrape_fireside_ventures() -> list[dict]:
    """Search for Fireside Ventures (India D2C/consumer focused fund)."""
    print("  Scraping Fireside Ventures portfolio...")
    queries = [
        "Fireside Ventures portfolio India 2024 2025 startups founders list",
        "site:firesideventures.in portfolio India startup 2024 2025",
        '"Fireside Ventures" India startup funded consumer D2C 2024 2025',
        '"Fireside Ventures" India startup "Series A" OR "seed" 2024 2025',
    ]
    results = []
    for q in queries:
        hits = google_search(q, 10)
        for h in hits:
            results.append({**h, "accelerator": "Fireside Ventures"})
    return results


def scrape_india_quotient() -> list[dict]:
    """Search for India Quotient (India-first consumer/vernacular fund)."""
    print("  Scraping India Quotient portfolio...")
    queries = [
        "India Quotient portfolio 2024 2025 startups founders list",
        "site:indiaquotient.in portfolio India startup 2024 2025",
        '"India Quotient" India startup funded consumer AI vernacular 2024 2025',
        '"India Quotient" India startup seed "Series A" 2024 2025',
    ]
    results = []
    for q in queries:
        hits = google_search(q, 10)
        for h in hits:
            results.append({**h, "accelerator": "India Quotient"})
    return results


def scrape_prime_venture_partners() -> list[dict]:
    """Search for Prime Venture Partners portfolio."""
    print("  Scraping Prime Venture Partners portfolio...")
    queries = [
        "Prime Venture Partners portfolio India 2024 2025 startups list",
        "site:primevp.in portfolio India startup 2024 2025",
        '"Prime Venture Partners" India startup funded AI health consumer 2024 2025',
        '"Prime VP" India startup seed "Series A" 2024 2025',
    ]
    results = []
    for q in queries:
        hits = google_search(q, 10)
        for h in hits:
            results.append({**h, "accelerator": "Prime Venture Partners"})
    return results


def scrape_fundamentum() -> list[dict]:
    """Search for Fundamentum Partnership (Nandan Nilekani's fund) portfolio."""
    print("  Scraping Fundamentum Partnership portfolio...")
    queries = [
        "Fundamentum Partnership portfolio India 2024 2025 startups founders",
        "site:fundamentum.vc portfolio India startup 2024 2025",
        '"Fundamentum" India startup funded AI health consumer SaaS 2024 2025',
        '"Fundamentum Partnership" India startup Series A B 2024 2025',
    ]
    results = []
    for q in queries:
        hits = google_search(q, 10)
        for h in hits:
            results.append({**h, "accelerator": "Fundamentum Partnership"})
    return results


def scrape_dsg_consumer_partners() -> list[dict]:
    """Search for DSG Consumer Partners (India consumer-focused VC)."""
    print("  Scraping DSG Consumer Partners portfolio...")
    queries = [
        "DSG Consumer Partners portfolio India 2024 2025 startups founders",
        '"DSG Consumer" India startup funded consumer D2C health 2024 2025',
        '"DSG Consumer Partners" India startup Series A seed 2024 2025',
    ]
    results = []
    for q in queries:
        hits = google_search(q, 10)
        for h in hits:
            results.append({**h, "accelerator": "DSG Consumer Partners"})
    return results


def scrape_arali_ventures() -> list[dict]:
    """Search for Arali Ventures (South India deep-tech/AI VC)."""
    print("  Scraping Arali Ventures portfolio...")
    queries = [
        "Arali Ventures portfolio India 2024 2025 startups founders list",
        "site:arali.vc portfolio India startup 2024 2025",
        '"Arali Ventures" India startup funded AI health deeptech 2024 2025',
    ]
    results = []
    for q in queries:
        hits = google_search(q, 10)
        for h in hits:
            results.append({**h, "accelerator": "Arali Ventures"})
    return results


def scrape_pravega_ventures() -> list[dict]:
    """Search for Pravega Ventures (early-stage India VC)."""
    print("  Scraping Pravega Ventures portfolio...")
    queries = [
        "Pravega Ventures portfolio India 2024 2025 startups founders list",
        '"Pravega Ventures" India startup funded AI health consumer 2024 2025',
        '"Pravega" India startup seed pre-seed 2024 2025',
    ]
    results = []
    for q in queries:
        hits = google_search(q, 10)
        for h in hits:
            results.append({**h, "accelerator": "Pravega Ventures"})
    return results


def scrape_all_in_capital() -> list[dict]:
    """Search for All In Capital (India-focused early-stage fund)."""
    print("  Scraping All In Capital portfolio...")
    queries = [
        "All In Capital India portfolio 2024 2025 startups founders",
        '"All In Capital" India startup funded AI health consumer 2024 2025',
        '"All In Capital" India startup pre-seed seed 2024 2025',
    ]
    results = []
    for q in queries:
        hits = google_search(q, 10)
        for h in hits:
            results.append({**h, "accelerator": "All In Capital"})
    return results


# ── Direct portfolio page reads via Cloudflare Browser Rendering ──────────────
# fetch_page() renders each URL with Cloudflare's headless Chrome (handles
# React/Next.js SPAs), falling back to Jina AI for static pages or when CF
# credentials are absent.  This captures companies that never appear in search.

PORTFOLIO_PAGES = {
    "Antler India":        "https://www.antler.co/location/india",
    "Blume Ventures":      "https://blume.vc/portfolio",
    "Better Capital":      "https://bettercapital.us/portfolio",
    "Fireside Ventures":   "https://www.firesideventures.in/portfolio",
    "India Quotient":      "https://indiaquotient.in/portfolio",
    "Prime VP":            "https://www.primevp.in/portfolio",
    "Kalaari Capital":     "https://www.kalaari.com/portfolio",
    "Stellaris VP":        "https://www.stellaris.in/portfolio",
    "3one4 Capital":       "https://www.3one4.com/portfolio",
    "Axilor Ventures":     "https://axilor.com/portfolio",
    "Titan Capital":       "https://www.titan.capital/portfolio",
    "T-Hub":               "https://t-hub.in/startups",
    "CIIE.CO":             "https://ciie.co/portfolio",
    "NSRCEL":              "https://nsrcel.org/portfolio",
    # JS-heavy pages that previously returned no content via Jina
    "Peak XV (Sequoia)":   "https://www.peakxv.com/portfolio",
    "Accel India":         "https://www.accel.com/portfolio?location=india",
    "Elevation Capital":   "https://elevationcapital.com/portfolio",
    "Nexus VP":            "https://www.nexusvp.com/portfolio",
    "Chiratae Ventures":   "https://www.chiratae.com/portfolio",
}

# Keep old name as alias so any external code referencing it still works
JINA_PORTFOLIO_PAGES = PORTFOLIO_PAGES


def scrape_portfolio_pages() -> list[dict]:
    """
    Render each portfolio page via Cloudflare Browser Rendering and extract
    startup names.  Falls back to Jina AI if CF credentials are not set.
    """
    print("  [Browser] Directly reading portfolio pages via CF Browser Rendering...")
    all_results = []
    for accel_name, url in PORTFOLIO_PAGES.items():
        print(f"    Fetching {accel_name}: {url}")
        page_text = fetch_page(url)
        if not page_text:
            print(f"    [!] No content for {accel_name}")
            continue
        startups = jina_extract_startups(page_text, accel_name)
        print(f"    Found {len(startups)} candidates from {accel_name}")
        all_results.extend(startups)
    return all_results


# Legacy alias used by run() below
scrape_jina_portfolios = scrape_portfolio_pages


def run():
    """Main entry point."""
    print("\n=== Accelerator Portfolio Scraper ===\n")

    all_results = []

    # ── Phase 0: Direct portfolio page reads (CF Browser Rendering → Jina fallback) ──
    print("[Phase 0] Direct portfolio page reads via Cloudflare Browser Rendering...")
    all_results.extend(scrape_jina_portfolios())

    all_results.extend(scrape_yc_india())
    all_results.extend(scrape_antler_india())
    all_results.extend(scrape_surge())
    all_results.extend(scrape_100x_vc())
    all_results.extend(scrape_techstars_india())
    all_results.extend(scrape_gsf_india())
    all_results.extend(scrape_500_startups_india())
    all_results.extend(scrape_plug_and_play_india())
    all_results.extend(scrape_iim_nasscom())
    all_results.extend(scrape_rocket_internet())
    # New accelerators
    all_results.extend(scrape_9unicorns())
    all_results.extend(scrape_axilor())
    all_results.extend(scrape_venture_catalysts())
    all_results.extend(scrape_better_capital())
    all_results.extend(scrape_first_cheque())
    all_results.extend(scrape_titan_capital())
    all_results.extend(scrape_kstart())
    all_results.extend(scrape_blume_founders_fund())

    # India Incubators
    all_results.extend(scrape_thub())
    all_results.extend(scrape_ciie())
    all_results.extend(scrape_nsrcel())
    all_results.extend(scrape_sine_iitb())
    all_results.extend(scrape_fitt_iitd())
    all_results.extend(scrape_kerala_startup_mission())
    all_results.extend(scrape_atal_innovation_mission())
    all_results.extend(scrape_tie_india())
    all_results.extend(scrape_f6s_india())
    all_results.extend(scrape_startup_india_dpiit())

    # More VC Portfolios
    all_results.extend(scrape_elevation_capital())
    all_results.extend(scrape_fireside_ventures())
    all_results.extend(scrape_india_quotient())
    all_results.extend(scrape_prime_venture_partners())
    all_results.extend(scrape_fundamentum())
    all_results.extend(scrape_dsg_consumer_partners())
    all_results.extend(scrape_arali_ventures())
    all_results.extend(scrape_pravega_ventures())
    all_results.extend(scrape_all_in_capital())

    # Deduplicate by URL.
    # Records from scrape_portfolio_pages() / jina_extract_startups() use
    # "website" not "url" - fall back gracefully to avoid KeyError.
    seen: set[str] = set()
    unique = []
    for r in all_results:
        raw_url = r.get("url") or r.get("website") or ""
        key = raw_url.split("?")[0].lower() if raw_url else ""
        if key not in seen:
            seen.add(key)
            unique.append(r)

    print(f"\nTotal unique accelerator results: {len(unique)}")

    output_path = Path(__file__).parent.parent / "data" / "accelerator_raw.json"
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(unique, f, indent=2, ensure_ascii=False)
    print(f"Saved to {output_path}")

    return unique


if __name__ == "__main__":
    run()
