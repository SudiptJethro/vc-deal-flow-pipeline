// ============================================
// MCA21 Scraper - Ministry of Corporate Affairs
// Finds recently incorporated Indian startups via:
//   - zaubacorp.com  (MCA21 aggregator, Google-indexed)
//   - tofler.in      (MCA21 aggregator)
//   - mca.gov.in     (direct)
// No API key needed - uses Serper/Google dorking
// ============================================

import { multiSearch } from './google-dorker';

export interface McaHit {
  url: string;
  company_name: string;
  cin?: string;
  city?: string;
  title: string;
  snippet: string;
}

const CITY_PATTERNS = [
  'Bengaluru', 'Mumbai', 'Delhi', 'Hyderabad', 'Chennai',
  'Pune', 'Ahmedabad', 'Kolkata', 'Noida', 'Gurugram',
];

export async function runMcaScraper(apiKey?: string, kv?: KVNamespace): Promise<McaHit[]> {
  // ── Zaubacorp queries (best MCA21 aggregator for Google dorking) ──
  const zaubacorpQueries = [
    'site:zaubacorp.com "private limited" "artificial intelligence" incorporated 2024',
    'site:zaubacorp.com "private limited" "technology" "health" incorporated 2024',
    'site:zaubacorp.com "private limited" "consumer" incorporated 2024 Bengaluru',
    'site:zaubacorp.com "private limited" "consumer" incorporated 2024 Mumbai',
    'site:zaubacorp.com "private limited" "fintech" incorporated 2024',
    'site:zaubacorp.com "private limited" "edtech" incorporated 2024 India',
    'site:zaubacorp.com "private limited" "healthtech" OR "medtech" incorporated 2024',
    'site:zaubacorp.com "private limited" "AI" "SaaS" incorporated 2024 India',
  ];

  // ── Tofler queries ──
  const toflerQueries = [
    'site:tofler.in "private limited" "AI" "technology" India incorporated 2024',
    'site:tofler.in "private limited" "health" "technology" India incorporated 2024',
    'site:tofler.in "private limited" "consumer" "technology" India incorporated 2024',
  ];

  // ── Direct MCA dorks ──
  const mcaQueries = [
    '"Ministry of Corporate Affairs" "private limited" "AI startup" India 2024 incorporated',
    'site:mca.gov.in "private limited" technology startup India 2024',
    '"CIN" "private limited" India "artificial intelligence" startup incorporated 2024',
    '"CIN" "private limited" India "consumer technology" startup incorporated 2024',
    '"CIN" "private limited" India "health technology" startup incorporated 2024',
  ];

  // Run city-specific queries to capture location data
  const cityQueries = CITY_PATTERNS.map(city =>
    `site:zaubacorp.com "private limited" "technology" incorporated 2024 "${city}"`
  );

  const allQueries = [...zaubacorpQueries, ...toflerQueries, ...mcaQueries, ...cityQueries];
  const results = await multiSearch(allQueries, 10, 2000, apiKey, kv);

  const seen = new Set<string>();
  const hits: McaHit[] = [];

  for (const r of results) {
    const isRelevant =
      r.url.includes('zaubacorp.com') ||
      r.url.includes('tofler.in') ||
      r.url.includes('mca.gov.in');

    if (!isRelevant) continue;

    const key = r.url.split('?')[0].toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);

    // Extract company name from title
    // Zaubacorp: "COMPANY NAME PRIVATE LIMITED - CIN..."
    // Tofler: "Company Name Private Limited | Tofler"
    let companyName = r.title
      .replace(/\s*[-|]\s*(?:CIN|Tofler|MCA|Company Details).*/i, '')
      .replace(/\s*PRIVATE LIMITED\s*/i, '')
      .trim();

    // Extract CIN if present (format: U/L + 5 digits + 2 letters + 4 digits + 3 letters + 6 digits)
    const cinMatch = r.snippet.match(/\b([UL]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6})\b/);
    const cin = cinMatch?.[1];

    // Extract city from snippet/title
    const text = `${r.title} ${r.snippet}`;
    const cityMatch = CITY_PATTERNS.find(c => new RegExp(c, 'i').test(text));

    hits.push({
      url: r.url.split('?')[0],
      company_name: companyName || 'Unknown',
      cin,
      city: cityMatch,
      title: r.title,
      snippet: r.snippet,
    });
  }

  return hits;
}
