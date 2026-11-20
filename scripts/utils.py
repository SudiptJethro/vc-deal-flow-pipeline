"""
Deal Flow Pipeline - Shared Search & Fetch Utility

Search:       Serper.dev API when SERPER_API_KEY is set, DuckDuckGo library otherwise.
Page fetch:   Cloudflare Browser Rendering (REST API) primary, Jina AI fallback.
              CF rendering handles JavaScript SPAs that Jina cannot render.
              Uses the same CF account/token already configured for D1.

All scrapers import from here.
"""

import os
import re
import time
import json
import urllib.parse
from config import REQUEST_DELAY_SECONDS

# ── Optional dependency guards ────────────────────────────────────────────────

try:
    from ddgs import DDGS
    _DDG_AVAILABLE = True
except ImportError:
    try:
        from duckduckgo_search import DDGS  # legacy fallback
        _DDG_AVAILABLE = True
    except ImportError:
        _DDG_AVAILABLE = False

try:
    import requests
    from bs4 import BeautifulSoup
    _REQUESTS_AVAILABLE = True
except ImportError:
    _REQUESTS_AVAILABLE = False


# ══════════════════════════════════════════════════════════════════════════════
# Search helpers
# ══════════════════════════════════════════════════════════════════════════════

def _serper_search(query: str, num_results: int) -> list[dict]:
    """
    Search via the Serper.dev Google Search API (official, paid API with a free tier).
    Used when SERPER_API_KEY is set. Returns [] if the key is missing or the call fails.
    """
    api_key = os.environ.get("SERPER_API_KEY", "").strip()
    if not api_key or not _REQUESTS_AVAILABLE:
        return []
    try:
        resp = requests.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
            json={"q": query, "num": num_results, "gl": "in", "hl": "en"},
            timeout=20,
        )
        resp.raise_for_status()
        return [
            {"title": r.get("title", ""), "url": r.get("link", ""), "snippet": r.get("snippet", "")}
            for r in resp.json().get("organic", [])
        ]
    except Exception as e:
        print(f"  [Serper] failed: {e}")
        return []


def _ddg_search(query: str, num_results: int) -> list[dict]:
    """
    DDG library search, used when no SERPER_API_KEY is configured.
    DDG often rejects site: queries from cloud IPs, so these are skipped.
    """
    import random
    # Skip site: queries, which DDG rejects from cloud IPs
    if "site:" in query.lower():
        return []
    try:
        with DDGS() as ddgs:
            results = []
            for r in ddgs.text(query, max_results=num_results):
                results.append({
                    "title":   r.get("title", ""),
                    "url":     r.get("href", ""),
                    "snippet": r.get("body", ""),
                })
            if results:
                time.sleep(random.uniform(1.0, 2.0))
            return results
    except Exception:
        return []


def web_search(query: str, num_results: int = 20) -> list[dict]:
    """
    Unified search, in priority order:
      1. Serper.dev API   (set SERPER_API_KEY; recommended for scheduled runs)
      2. DDG library      (no key needed; good for local runs)
    Returns list of {title, url, snippet}.
    """
    if os.environ.get("SERPER_API_KEY", "").strip():
        return _serper_search(query, num_results)
    if _DDG_AVAILABLE:
        return _ddg_search(query, num_results)
    return []


# Alias so existing scrapers can do `from utils import web_search as google_search`
google_search = web_search


# ══════════════════════════════════════════════════════════════════════════════
# Cloudflare Browser Rendering  (via Worker /api/render endpoint)
# ══════════════════════════════════════════════════════════════════════════════
#
# Browser Rendering runs INSIDE the Cloudflare Worker as a native Puppeteer
# binding (@cloudflare/puppeteer).  The Worker exposes a POST /api/render
# endpoint that accepts a URL, renders it with headless Chrome on the CF edge,
# and returns the fully executed HTML - perfect for React/Next.js SPA pages.
#
# Required env vars (same secrets already configured for D1):
#   WORKER_URL       - e.g. https://deal-flow-pipeline.<subdomain>.workers.dev
#   PIPELINE_SECRET  - Bearer token (same as PIPELINE_SECRET in the Worker)
#
# ══════════════════════════════════════════════════════════════════════════════


def _worker_credentials() -> tuple[str, str]:
    """Return (worker_url, pipeline_secret) from environment, stripped of whitespace."""
    return (
        os.environ.get("WORKER_URL", "").strip().rstrip("/"),
        os.environ.get("PIPELINE_SECRET", "").strip(),
    )


def cf_browser_fetch(url: str, wait_ms: int = 2000, timeout: int = 35) -> str:
    """
    Render a URL using the Cloudflare Worker's /api/render endpoint, which uses
    @cloudflare/puppeteer (headless Chrome) on the CF edge network.

    Args:
        url:     Page to render.
        wait_ms: Extra settle time (ms) after networkidle for lazy content.
        timeout: HTTP request timeout in seconds (Worker has 25 s internal cap).

    Returns:
        Rendered HTML string, or "" on failure / missing Worker URL.
    """
    if not _REQUESTS_AVAILABLE:
        return ""

    worker_url, secret = _worker_credentials()
    if not worker_url:
        return ""

    endpoint = f"{worker_url}/api/render"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {secret}",
    }
    payload = {"url": url, "waitMs": wait_ms}

    try:
        resp = requests.post(endpoint, headers=headers, json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        if data.get("ok"):
            html = data.get("data", {}).get("html", "")
            time.sleep(1)
            return html
        else:
            print(f"  [CF Browser] Worker error for {url}: {data.get('error')}")
    except Exception as e:
        print(f"  [CF Browser] Failed to render {url}: {e}")

    return ""


def cf_browser_fetch_text(url: str, **kwargs) -> str:
    """
    Render a URL via Cloudflare Browser Rendering and return clean visible text
    (HTML tags stripped). Useful for keyword scanning and startup extraction.
    """
    html = cf_browser_fetch(url, **kwargs)
    if not html:
        return ""
    if not _REQUESTS_AVAILABLE:
        return re.sub(r"<[^>]+>", " ", html)
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "meta", "link", "svg"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)


def fetch_page(url: str) -> str:
    """
    Smart page fetcher:
      1. Cloudflare Browser Rendering  - renders full JS/SPA pages via CF edge.
      2. Jina AI Reader                - fallback for when CF creds are absent.

    Returns rendered text content (tags stripped).
    """
    text = cf_browser_fetch_text(url)
    if text and len(text) > 200:
        return text

    # CF not configured or returned nothing - fall back to Jina markdown
    if text == "" and _worker_credentials()[0]:
        print(f"  [Fetch] CF Browser gave no content, falling back to Jina for {url}")
    return jina_read(url)


# ══════════════════════════════════════════════════════════════════════════════
# Jina AI Reader  (static fallback - no JS rendering)
# ══════════════════════════════════════════════════════════════════════════════

JINA_BASE = "https://r.jina.ai/"


def jina_read(url: str, timeout: int = 20) -> str:
    """
    Fetch any webpage as clean markdown via Jina AI Reader (free, no API key).
    Good for static/server-rendered pages. Returns empty string on failure.
    """
    if not _REQUESTS_AVAILABLE:
        return ""
    try:
        resp = requests.get(
            f"{JINA_BASE}{url}",
            headers={"Accept": "text/plain"},
            timeout=timeout,
        )
        resp.raise_for_status()
        time.sleep(1)
        return resp.text
    except Exception as e:
        print(f"  [Jina] failed to read {url}: {e}")
        return ""


# ══════════════════════════════════════════════════════════════════════════════
# Startup name extraction from rendered page text (regex heuristics)
# ══════════════════════════════════════════════════════════════════════════════

def jina_extract_startups(page_text: str, accelerator: str) -> list[dict]:
    """
    Extract startup/company names from rendered page text using regex heuristics.
    Works on both Jina markdown output and plain text from CF browser rendering.

    Returns list of raw dicts compatible with the enricher.
    """
    results = []
    seen = set()

    patterns = [
        r"^#{1,3}\s+([A-Z][A-Za-z0-9\s\.\-]{2,40})",
        r"\*\*([A-Z][A-Za-z0-9\s\.\-]{2,40})\*\*",
        r"^\s*[-*]\s+([A-Z][A-Za-z0-9\s\.\-]{2,40})",
        r"\[([A-Z][A-Za-z0-9\s\.\-]{2,40})\]\(https?://",
    ]

    skip_words = {
        "Home", "About", "Portfolio", "Team", "Contact", "Blog",
        "News", "Menu", "Skip", "Login", "Sign", "Apply", "Learn",
        "More", "Read", "View", "Back", "Next", "Previous", "The",
        "India", "Startups", "Companies", "Programs", "Cohort",
    }
    skip_lower = {w.lower() for w in skip_words}

    for line in page_text.splitlines():
        for pat in patterns:
            for m in re.finditer(pat, line, re.MULTILINE):
                name = m.group(1).strip().rstrip(".,:")
                if len(name) < 3 or len(name) > 50:
                    continue
                if name in skip_words or name.lower() in skip_lower:
                    continue
                key = name.lower()
                if key not in seen:
                    seen.add(key)
                    results.append({
                        "startup_name": name,
                        "founder_name": "",
                        "linkedin_url": None,
                        "website": None,
                        "one_liner": f"Discovered via {accelerator} portfolio page",
                        "source": f"browser:{accelerator}",
                        "founded_year": 2024,
                    })

    return results
