// ============================================
// Accelerator Portfolio Scraper via Google Dorking
// YC, Antler India, SURGE, 100X.VC
// ============================================

import { multiSearch } from './google-dorker';
import type { SearchResult } from '../types';

export interface AcceleratorHit extends SearchResult {
  accelerator: string;
}

async function scrapeAccelerator(name: string, queries: string[], apiKey?: string, kv?: KVNamespace): Promise<AcceleratorHit[]> {
  const results = await multiSearch(queries, 10, 2000, apiKey, kv);
  return results.map(r => ({ ...r, accelerator: name }));
}

export async function scrapeYCIndia(apiKey?: string, kv?: KVNamespace): Promise<AcceleratorHit[]> {
  return scrapeAccelerator('YC', [
    'Y Combinator India startups 2024 batch list founders',
    'Y Combinator India startups 2025 batch consumer AI health',
    'YC W24 S24 India founders startups',
    'YC W25 S25 India founders startups',
    'site:ycombinator.com/companies India consumer AI health 2024',
  ], apiKey, kv);
}

export async function scrapeAntlerIndia(apiKey?: string, kv?: KVNamespace): Promise<AcceleratorHit[]> {
  return scrapeAccelerator('Antler India', [
    'Antler India portfolio 2024 startups founders list',
    'Antler India cohort 2024 consumer AI healthtech',
    'site:antler.co India portfolio startups',
    'Antler India invested startups 2024 2025',
  ], apiKey, kv);
}

export async function scrapeSurge(apiKey?: string, kv?: KVNamespace): Promise<AcceleratorHit[]> {
  return scrapeAccelerator('SURGE', [
    'SURGE accelerator India portfolio 2024 startups',
    'Peak XV SURGE cohort 2024 2025 India startups',
    'Sequoia SURGE India startups consumer AI health',
    'site:peakxv.com surge startups India',
  ], apiKey, kv);
}

export async function scrape100XVC(apiKey?: string, kv?: KVNamespace): Promise<AcceleratorHit[]> {
  return scrapeAccelerator('100X.VC', [
    '100X.VC portfolio 2024 India startups consumer AI health',
    '100X.VC batch 2024 startups list founders',
  ], apiKey, kv);
}

export async function runAcceleratorScraper(apiKey?: string, kv?: KVNamespace): Promise<AcceleratorHit[]> {
  const yc      = await scrapeYCIndia(apiKey, kv);
  const antler  = await scrapeAntlerIndia(apiKey, kv);
  const surge   = await scrapeSurge(apiKey, kv);
  const hundredx = await scrape100XVC(apiKey, kv);

  const seen = new Set<string>();
  return [...yc, ...antler, ...surge, ...hundredx].filter(r => {
    const key = r.url.split('?')[0].toLowerCase();
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}
