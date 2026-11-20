// ============================================
// Google Search via the Serper.dev API
// KV caches results per query for 24 hours to save API quota
// ============================================

import type { SearchResult } from '../types';

const CACHE_TTL_SECONDS = 60 * 60 * 24; // 24 hours

function cacheKey(query: string): string {
  // Simple deterministic key, safe for KV
  return `search:${query.toLowerCase().replace(/\s+/g, '_').slice(0, 200)}`;
}

// ── Serper.dev API ──

async function serperSearch(query: string, numResults: number, apiKey: string): Promise<SearchResult[]> {
  try {
    const resp = await fetch('https://google.serper.dev/search', {
      method: 'POST',
      headers: { 'X-API-KEY': apiKey, 'Content-Type': 'application/json' },
      body: JSON.stringify({ q: query, num: numResults, gl: 'in', hl: 'en' }),
    });
    if (!resp.ok) {
      console.log(`Serper failed (${resp.status}): ${query.slice(0, 60)}`);
      return [];
    }
    const data = await resp.json<{
      organic?: Array<{ title: string; link: string; snippet?: string }>;
    }>();
    return (data.organic ?? []).map(r => ({ title: r.title, url: r.link, snippet: r.snippet ?? '' }));
  } catch (e) {
    console.log(`Serper error: ${e}`);
    return [];
  }
}

// ── Public API ──

export async function googleSearch(
  query: string,
  numResults = 10,
  apiKey?: string,
  kv?: KVNamespace
): Promise<SearchResult[]> {
  // Check KV cache first
  if (kv) {
    const cached = await kv.get(cacheKey(query));
    if (cached) {
      try {
        return JSON.parse(cached) as SearchResult[];
      } catch {
        // stale/corrupt cache entry - fall through to live fetch
      }
    }
  }

  // Requires a Serper.dev API key; without one, no search is performed.
  const results = apiKey ? await serperSearch(query, numResults, apiKey) : [];

  // Write to KV cache
  if (kv && results.length > 0) {
    await kv.put(cacheKey(query), JSON.stringify(results), { expirationTtl: CACHE_TTL_SECONDS });
  }

  return results;
}

export async function multiSearch(
  queries: string[],
  resultsPerQuery = 10,
  delayMs = 1500,
  apiKey?: string,
  kv?: KVNamespace
): Promise<SearchResult[]> {
  const all: SearchResult[] = [];
  const seen = new Set<string>();

  for (const q of queries) {
    const results = await googleSearch(q, resultsPerQuery, apiKey, kv);
    for (const r of results) {
      const key = r.url.split('?')[0].toLowerCase();
      if (!seen.has(key)) {
        seen.add(key);
        all.push(r);
      }
    }
    // No delay when using Serper (server-side rate limiting); delay for HTML scraping
    if (delayMs > 0 && !apiKey) {
      await new Promise(resolve => setTimeout(resolve, delayMs));
    }
  }

  return all;
}
