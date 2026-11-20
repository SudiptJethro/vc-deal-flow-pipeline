"""
Deal Flow Pipeline - Enricher
Takes raw scraper results and enriches them with:
  1. Founder LinkedIn URLs (via Google dorking)
  2. Sector classification
  3. Tier assignment
  4. Deduplication against existing data
"""

import json
import re
from pathlib import Path

from config import (
    SECTOR_KEYWORDS, EXCLUDED_STARTUPS, PREMIER_INSTITUTIONS,
    TOP_COMPANIES
)
from utils import web_search as google_search  # Serper API if configured, else DDG


_LI_URL_RE = re.compile(r'linkedin\.com/in/([\w\-]+)')

# ── Funding stage inference ────────────────────────────────────────────────────

# Ordered most-specific → least-specific; first match wins.
_FUNDING_PATTERNS = [
    (re.compile(r'\bseries[- ]?[bcd]\b|\bseries[- ]?[bcd]\+', re.I), 'Series B+'),
    (re.compile(r'\bseries[- ]?a\b',                                   re.I), 'Series A'),
    (re.compile(
        r'\bseed[- ]?funded\b|\bseed[- ]?round\b|\braised[\w ,]+seed\b'
        r'|\bseed[- ]?stage\b|\bcompleted seed\b|\bclosed seed\b',       re.I), 'Seed'),
    (re.compile(r'\braised\s+[\$₹]\d', re.I), 'Seed'),   # "raised $500k" / "raised ₹2Cr"
    (re.compile(r'\bangel[- ]?funded\b|\bangel[- ]?round\b|\bangel[- ]?backed\b', re.I), 'Angel'),
    (re.compile(r'\bpre[- ]?seed\b',  re.I), 'Pre-Seed'),
    (re.compile(r'\bbootstrapped\b|\bself[- ]?funded\b|\bunfunded\b',    re.I), 'Unfunded'),
    (re.compile(
        r'\braising\b|\bopen to (funding|investment|raise)\b'
        r'|\bseeking (investment|funding)\b|\blooking (to raise|for funding)\b',
        re.I), 'Seeking Pre-Seed'),
]

# Source prefix → implied stage (used when text signals are absent)
_SOURCE_STAGE_MAP = [
    ('yc',              'Seed'),       # YC invests at seed
    ('y_combinator',    'Seed'),
    ('surge',           'Seed'),       # Sequoia Surge is seed
    ('antler',          'Pre-Seed'),   # Antler is pre-seed
    ('techstars',       'Pre-Seed'),
    ('gsf',             'Pre-Seed'),
    ('100x',            'Pre-Seed'),
    ('9unicorns',       'Pre-Seed'),
    ('axilor',          'Pre-Seed'),
    ('accelerator:',    'Pre-Seed'),   # catch-all accelerator prefix
    ('linkedin:building_post', 'Seeking Pre-Seed'),
    ('twitter_building',       'Seeking Pre-Seed'),
    ('reddit:',                'Seeking Pre-Seed'),
    ('hn:',                    'Seeking Pre-Seed'),
    ('producthunt',            'Seeking Pre-Seed'),
]


def infer_funding_stage(raw: dict) -> str:
    """
    Infer funding stage from text signals in one_liner/snippet/rationale,
    then fall back to source-based defaults, then to 'Seeking Pre-Seed'.
    """
    text = ' '.join(filter(None, [
        raw.get('one_liner', ''),
        raw.get('snippet', ''),
        raw.get('tier_rationale', ''),
        raw.get('tagline', ''),
    ]))

    for pattern, stage in _FUNDING_PATTERNS:
        if pattern.search(text):
            return stage

    source = (raw.get('source') or '').lower()
    for key, stage in _SOURCE_STAGE_MAP:
        if key in source:
            return stage

    return 'Seeking Pre-Seed'  # reasonable default for early-stage pipeline


def find_linkedin_url(founder_name: str, startup_name: str = None) -> str | None:
    """Find a founder's personal LinkedIn profile via broad search.

    Avoids site:linkedin.com/in - LinkedIn de-indexes most profiles so that
    operator returns nothing.  Instead searches by name and checks both result
    URLs and snippets for embedded LinkedIn profile links.
    """
    parts = [f'"{founder_name}"']
    if startup_name and startup_name != "Stealth Startup":
        parts.append(f'"{startup_name}"')
    parts.append("founder OR co-founder OR CEO linkedin")

    query = " ".join(parts)
    results = google_search(query, 5)

    for r in results:
        url = r.get("url", "")
        if "linkedin.com/in/" in url:
            return url.split("?")[0]
        m = _LI_URL_RE.search(r.get("snippet", "") + " " + r.get("title", ""))
        if m:
            return f"https://www.linkedin.com/in/{m.group(1)}"

    return None


def classify_sector(text: str) -> str:
    """Classify a startup into a sector based on keywords in its description."""
    text_lower = text.lower()

    scores = {}
    for sector, keywords in SECTOR_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        scores[sector] = score

    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return "Consumer Tech"  # default
    return best


def assign_tier(founder_info: dict) -> tuple[int, str]:
    """
    Assign tier 1/2/3 based on founder background.
    Returns (tier, rationale).
    """
    text = " ".join([
        founder_info.get("background", ""),
        founder_info.get("snippet", ""),
        founder_info.get("title", ""),
    ]).lower()

    # Drop site-name boilerplate such as "Jane Doe | LinkedIn" or "... - LinkedIn",
    # so the page's host is not mistaken for the founder's former employer.
    text = re.sub(r"\s[|\u00b7\u2013-]\s*linkedin\b", " ", text)
    text = re.sub(r"\S*linkedin\.com\S*", " ", text)

    def has(term: str) -> bool:
        # Whole-word match, so "MIT" does not fire on "submit" or "arr" on "carry".
        return re.search(r"(?<![a-z0-9])" + re.escape(term.lower()) + r"(?![a-z0-9])", text) is not None

    # Tier 1 checks
    for inst in PREMIER_INSTITUTIONS:
        if has(inst):
            return 1, f"{inst} alumni"

    for company in TOP_COMPANIES:
        if has(company):
            return 1, f"Ex-{company}"

    traction_signals = ["series a", "series b", "million users", "revenue", "arr", "unicorn"]
    for signal in traction_signals:
        if has(signal):
            return 1, f"Strong traction ({signal})"

    # Tier 2 checks
    tier2_signals = ["raised", "seed", "pre-seed", "backed by", "accelerator", "yc", "antler", "surge"]
    for signal in tier2_signals:
        if has(signal):
            return 2, "Some funding/accelerator signals"

    # Default: Tier 3
    return 3, "Early stage, limited public info"


def is_excluded(startup_name: str) -> bool:
    """Check if startup is in the exclusion list."""
    return startup_name.strip() in EXCLUDED_STARTUPS


def extract_name_from_linkedin_slug(linkedin_url: str) -> str:
    """Extract a best-guess founder name from a LinkedIn profile URL slug."""
    try:
        slug = linkedin_url.split("/in/")[-1].rstrip("/").split("?")[0]
        slug = re.sub(r"-\d+$", "", slug)          # strip trailing numeric suffix
        parts = [p for p in slug.split("-") if p]
        if len(parts) >= 2:
            return " ".join(p.capitalize() for p in parts[:3])
    except Exception:
        pass
    return ""


def enrich_startup(raw: dict) -> dict | None:
    """
    Take a raw scraper result and enrich it into the final schema.
    Returns None if the startup should be excluded.
    """
    startup_name = raw.get("startup_name", raw.get("name", "Unknown"))

    if is_excluded(startup_name):
        return None

    founder_name = raw.get("founder_name", "")
    linkedin_url = raw.get("linkedin_url")

    # If we have a LinkedIn URL but no name, try extracting from the slug
    if linkedin_url and not founder_name:
        founder_name = extract_name_from_linkedin_slug(linkedin_url)

    # Find LinkedIn if not already present
    if not linkedin_url and founder_name:
        print(f"  Enriching LinkedIn for {founder_name}...")
        linkedin_url = find_linkedin_url(founder_name, startup_name)

    # Classify sector
    description = " ".join(filter(None, [
        raw.get("one_liner", ""),
        raw.get("snippet", ""),
        raw.get("tagline", ""),
        startup_name,
    ]))
    sector = raw.get("sector") or classify_sector(description)

    # Assign tier
    tier, rationale = assign_tier(raw)
    if raw.get("tier"):
        tier = raw["tier"]
    if raw.get("tier_rationale"):
        rationale = raw["tier_rationale"]

    # For LinkedIn-profile-only records where we still don't have a startup name,
    # use the URL slug as a stable unique identifier so D1's unique constraint
    # (founder_name, startup_name) doesn't collapse all of them into one row.
    if startup_name == "Unknown" and linkedin_url:
        slug = linkedin_url.split("/in/")[-1].rstrip("/").split("?")[0]
        startup_name = f"[Profile] {slug}"

    funding_stage = raw.get("funding_stage") or infer_funding_stage(raw)

    return {
        "founder_name": founder_name,
        "startup_name": startup_name,
        "linkedin_url": linkedin_url,
        "website": raw.get("website"),
        "sector": sector,
        "one_liner": raw.get("one_liner", raw.get("tagline", raw.get("snippet", "")))[:120],
        "tier": tier,
        "tier_rationale": rationale[:100],
        "source": raw.get("source", "Enricher"),
        "founded_year": raw.get("founded_year", 2024),
        "city": raw.get("city"),
        "funding_stage": funding_stage,
        "is_new": False,  # set to True by merge_with_existing() for genuinely new entries
    }


_PLACEHOLDER_NAMES = {"unknown", "stealth startup", ""}


def merge_with_existing(new_entries: list[dict], existing_path: str) -> list[dict]:
    """Merge new entries with existing startups.json.

    Deduplication strategy:
    - Named startups:  deduplicated by startup_name (case-insensitive).
    - LinkedIn-profile-only records (startup_name is a placeholder):
      deduplicated by linkedin_url so every unique profile is kept.
    """
    existing = []
    if Path(existing_path).exists():
        with open(existing_path, "r", encoding="utf-8") as f:
            existing = json.load(f)

    # Clear is_new from all existing entries - they were new last run, not this one
    for e in existing:
        e["is_new"] = False

    seen_names = {
        e["startup_name"].lower().strip()
        for e in existing
        if e.get("startup_name", "").lower().strip() not in _PLACEHOLDER_NAMES
    }
    seen_linkedin = {
        e["linkedin_url"].lower().rstrip("/")
        for e in existing
        if e.get("linkedin_url")
    }

    merged = list(existing)
    added = 0
    for entry in new_entries:
        name_key = entry.get("startup_name", "").lower().strip()
        linkedin_key = (entry.get("linkedin_url") or "").lower().rstrip("/")

        if name_key not in _PLACEHOLDER_NAMES:
            # Named startup - dedupe by name
            if name_key in seen_names or is_excluded(entry.get("startup_name", "")):
                continue
            seen_names.add(name_key)
        else:
            # Profile-only record - dedupe by LinkedIn URL
            if not linkedin_key or linkedin_key in seen_linkedin:
                continue

        if linkedin_key:
            seen_linkedin.add(linkedin_key)
        entry["is_new"] = True   # tag - cleared on the next run's merge
        merged.append(entry)
        added += 1

    print(f"  Merged: {added} new entries added ({len(merged)} total)")
    return merged


def run(raw_files: list[str] = None):
    """Main entry point."""
    print("\n=== Enricher ===\n")

    data_dir = Path(__file__).parent.parent / "data"

    if not raw_files:
        raw_files = list(data_dir.glob("*_raw.json"))
    else:
        raw_files = [Path(f) for f in raw_files]

    all_raw = []
    for rf in raw_files:
        if rf.exists():
            with open(rf, "r", encoding="utf-8") as f:
                entries = json.load(f)
                all_raw.extend(entries)
                print(f"  Loaded {len(entries)} from {rf.name}")

    print(f"\nTotal raw entries: {len(all_raw)}")

    # Enrich each entry
    enriched = []
    for raw in all_raw:
        result = enrich_startup(raw)
        if result:
            enriched.append(result)

    print(f"Enriched entries: {len(enriched)}")

    # Merge with existing
    existing_path = data_dir / "startups.json"
    merged = merge_with_existing(enriched, str(existing_path))

    # Save
    with open(existing_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(merged)} startups to {existing_path}")

    return merged


if __name__ == "__main__":
    run()
