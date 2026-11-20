// ============================================
// Product Hunt Scraper via Google Dorking
// ============================================

import { multiSearch } from './google-dorker';

export interface ProductHuntHit {
  producthunt_url: string;
  title: string;
  snippet: string;
  tagline: string;
}

export async function runProductHuntScraper(apiKey?: string, kv?: KVNamespace): Promise<ProductHuntHit[]> {
  const queries = [
    'site:producthunt.com/posts "India" "AI" 2024',
    'site:producthunt.com/posts "India" "health" 2024',
    'site:producthunt.com/posts "India" "consumer" 2024',
    'site:producthunt.com/posts "India" "AI" 2025',
    'site:producthunt.com/posts "India" "productivity" "AI" 2024',
    'site:producthunt.com/posts "India" "fintech" 2024',
  ];

  const results = await multiSearch(queries, 10, 2000, apiKey, kv);

  const seen = new Set<string>();
  const hits: ProductHuntHit[] = [];
  for (const r of results) {
    if (r.url.includes('producthunt.com/posts/') || r.url.includes('producthunt.com/p/')) {
      const key = r.url.split('?')[0].toLowerCase();
      if (!seen.has(key)) {
        seen.add(key);
        const dashIdx = r.title.lastIndexOf(' - ');
        const tagline = dashIdx > 0 ? r.title.slice(dashIdx + 3).replace(/\s*\|\s*Product Hunt.*$/i, '') : '';
        hits.push({ producthunt_url: r.url.split('?')[0], title: r.title, snippet: r.snippet, tagline });
      }
    }
  }
  return hits;
}
