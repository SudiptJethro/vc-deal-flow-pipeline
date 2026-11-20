// ============================================
// Twitter/X Scraper via Google Dorking
// ============================================

import { multiSearch } from './google-dorker';

export interface TwitterHit {
  twitter_url: string;
  title: string;
  snippet: string;
  query_source: string;
}

export async function runTwitterScraper(apiKey?: string, kv?: KVNamespace): Promise<TwitterHit[]> {
  const queries = [
    // Building / stealth
    'site:twitter.com "building" "startup" "India" "AI" 2024',
    'site:twitter.com "building" "startup" "India" "consumer" 2025',
    'site:twitter.com "building" "startup" "India" "health" 2024',
    'site:x.com "I\'m building" "India" "AI" founder 2024',
    'site:x.com "quit my job" "building" "India" startup 2024',
    'site:twitter.com "launched" "India" "startup" "AI" 2025',
    'site:twitter.com "stealth" "founder" "India" "building" 2024',
    'site:x.com "ex-Swiggy" OR "ex-Razorpay" OR "ex-CRED" founder building',
    // Unfunded / pre-seed seeking
    'site:x.com "pre-seed" "raising" "India" founder startup 2024',
    'site:twitter.com "looking for investors" "India" startup founder 2024',
    'site:x.com "bootstrapped" "India" "AI" founder startup 2024',
    'site:x.com "unfunded" "India" founder building startup 2024',
    'site:twitter.com "angel investors" "India" "pre-seed" startup 2024',
    'site:x.com "raising" "pre-seed" "India" "AI" OR "health" OR "consumer" 2025',
    'site:x.com "DM me" "investors" "India" startup founder 2024',
  ];

  const results = await multiSearch(queries, 10, 2000, apiKey, kv);

  const seen = new Set<string>();
  const hits: TwitterHit[] = [];
  for (const r of results) {
    if (r.url.includes('twitter.com/') || r.url.includes('x.com/')) {
      const key = r.url.split('?')[0].toLowerCase();
      if (!seen.has(key)) {
        seen.add(key);
        hits.push({ twitter_url: r.url, title: r.title, snippet: r.snippet, query_source: 'twitter_search' });
      }
    }
  }
  return hits;
}
