// ============================================
// LinkedIn Scraper via Google Dorking
// ============================================

import { multiSearch } from './google-dorker';
import { MAFIA_COMPANIES } from '../config';

export interface LinkedInHit {
  linkedin_url: string;
  title: string;
  snippet: string;
  query_source: string;
}

export async function searchBuildingFounders(apiKey?: string, kv?: KVNamespace): Promise<LinkedInHit[]> {
  const queries = [
    // Building / stealth
    'site:linkedin.com/in "I\'m building" "India" "AI" 2024',
    'site:linkedin.com/in "I\'m building" "India" "health" 2024',
    'site:linkedin.com/in "I\'m building" "India" "consumer" 2025',
    'site:linkedin.com/in "founder" "building" "India" "stealth" 2024',
    'site:linkedin.com/in "co-founder" "stealth" "India" "AI" 2025',
    'site:linkedin.com/in "quit" "building" "India" "startup" 2024',
    // Actively seeking pre-seed / unfunded
    'site:linkedin.com/in "looking for" "pre-seed" "India" founder 2024',
    'site:linkedin.com/in "raising" "pre-seed" "India" startup 2024',
    'site:linkedin.com/in "seeking investment" "India" "AI" founder 2024',
    'site:linkedin.com/in "open to investors" "India" founder startup 2025',
    'site:linkedin.com/in "bootstrapped" "India" founder "AI" 2024',
    'site:linkedin.com/in "unfunded" "India" founder startup 2024',
    'site:linkedin.com/in "angel round" "India" founder startup 2024',
    'site:linkedin.com/in "pitching" "India" "pre-seed" founder 2024',
  ];
  const results = await multiSearch(queries, 10, 2000, apiKey, kv);
  return results
    .filter(r => r.url.includes('linkedin.com/in/'))
    .map(r => ({ linkedin_url: r.url.split('?')[0], title: r.title, snippet: r.snippet, query_source: 'building_post' }));
}

export async function searchExEmployeeFounders(companies?: string[], apiKey?: string, kv?: KVNamespace): Promise<LinkedInHit[]> {
  const targets = companies ?? MAFIA_COMPANIES.slice(0, 8);
  const queries = targets.map(c => `site:linkedin.com/in "ex-${c}" founder startup India`);
  const results = await multiSearch(queries, 8, 2000, apiKey, kv);
  return results
    .filter(r => r.url.includes('linkedin.com/in/'))
    .map(r => ({ linkedin_url: r.url.split('?')[0], title: r.title, snippet: r.snippet, query_source: 'ex_employee' }));
}

export async function searchInstitutionFounders(apiKey?: string, kv?: KVNamespace): Promise<LinkedInHit[]> {
  const institutions = ['IIT Bombay', 'IIT Delhi', 'IIT Madras', 'BITS Pilani', 'IIM Ahmedabad', 'ISB Hyderabad'];
  const queries = institutions.map(inst => `site:linkedin.com/in "${inst}" founder startup India 2024`);
  const results = await multiSearch(queries, 8, 2000, apiKey, kv);
  return results
    .filter(r => r.url.includes('linkedin.com/in/'))
    .map(r => ({ linkedin_url: r.url.split('?')[0], title: r.title, snippet: r.snippet, query_source: 'institution' }));
}

export async function findLinkedInUrl(
  founderName: string,
  startupName?: string,
  apiKey?: string,
  kv?: KVNamespace
): Promise<string | null> {
  let query = `site:linkedin.com/in "${founderName}"`;
  if (startupName && startupName !== 'Stealth Startup') query += ` "${startupName}"`;
  query += ' founder OR co-founder OR CEO';
  const results = await multiSearch([query], 3, 0, apiKey, kv);
  return results.find(r => r.url.includes('linkedin.com/in/'))?.url.split('?')[0] ?? null;
}

export async function runLinkedInScraper(apiKey?: string, kv?: KVNamespace): Promise<LinkedInHit[]> {
  const [building, exEmployee, institution] = await Promise.all([
    searchBuildingFounders(apiKey, kv),
    searchExEmployeeFounders(undefined, apiKey, kv),
    searchInstitutionFounders(apiKey, kv),
  ]);

  const seen = new Set<string>();
  const all: LinkedInHit[] = [];
  for (const hit of [...building, ...exEmployee, ...institution]) {
    const key = hit.linkedin_url.toLowerCase().replace(/\/$/, '');
    if (!seen.has(key)) { seen.add(key); all.push(hit); }
  }
  return all;
}
