// ============================================
// Crunchbase Scraper via Google Dorking
// ============================================

import { multiSearch } from './google-dorker';

export interface CrunchbaseHit {
  crunchbase_url: string;
  org_slug: string;
  title: string;
  snippet: string;
}

export async function runCrunchbaseScraper(apiKey?: string, kv?: KVNamespace): Promise<CrunchbaseHit[]> {
  const queries = [
    // Seed stage
    'site:crunchbase.com/organization "India" "consumer" "AI" "seed" 2024',
    'site:crunchbase.com/organization "India" "health" "seed" 2024',
    'site:crunchbase.com/organization "India" "consumer" "pre-seed" 2024',
    'site:crunchbase.com/organization "Bengaluru" "AI" "seed" 2024',
    'site:crunchbase.com/organization "Mumbai" "consumer" "seed" 2025',
    'site:crunchbase.com/organization "India" "mental health" "seed" 2024',
    'site:crunchbase.com/organization "India" "edtech" "AI" "seed" 2024',
    'site:crunchbase.com/organization "India" "consumer tech" "pre-seed" 2025',
    // Unfunded - key for pre-seed VC sourcing
    'site:crunchbase.com/organization "India" "AI" "unfunded" 2024',
    'site:crunchbase.com/organization "India" "consumer" "unfunded" 2024',
    'site:crunchbase.com/organization "India" "health" "unfunded" 2024',
    'site:crunchbase.com/organization "India" "unfunded" "technology" 2025',
    'site:crunchbase.com/organization "India" "pre-seed" "AI" 2025',
    'site:crunchbase.com/organization "India" "pre-seed" "health" 2024',
    'site:crunchbase.com/organization "India" "pre-seed" "consumer" 2025',
    'site:crunchbase.com/organization "Bengaluru" "unfunded" 2024',
    'site:crunchbase.com/organization "Mumbai" "unfunded" 2024',
  ];

  const results = await multiSearch(queries, 10, 2000, apiKey, kv);

  const seen = new Set<string>();
  const hits: CrunchbaseHit[] = [];
  for (const r of results) {
    if (r.url.includes('crunchbase.com/organization/')) {
      const orgSlug = r.url.split('/organization/')[1]?.split('/')[0]?.split('?')[0];
      if (orgSlug && !seen.has(orgSlug)) {
        seen.add(orgSlug);
        hits.push({ crunchbase_url: r.url.split('?')[0], org_slug: orgSlug, title: r.title, snippet: r.snippet });
      }
    }
  }
  return hits;
}
