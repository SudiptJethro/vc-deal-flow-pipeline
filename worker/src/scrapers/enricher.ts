// ============================================
// Enricher - classify sector, assign tier, find LinkedIn URLs
// ============================================

import { SECTOR_KEYWORDS, PREMIER_INSTITUTIONS, TOP_COMPANIES } from '../config';
import { findLinkedInUrl } from './linkedin';
import type { Startup, Sector, Tier } from '../types';

/**
 * Classify text into a sector based on keyword matching.
 */
export function classifySector(text: string): Sector {
  const lower = text.toLowerCase();
  const scores: Record<string, number> = {};

  for (const [sector, keywords] of Object.entries(SECTOR_KEYWORDS)) {
    scores[sector] = keywords.filter(kw => lower.includes(kw)).length;
  }

  const best = Object.entries(scores).reduce((a, b) => (b[1] > a[1] ? b : a));
  return (best[1] > 0 ? best[0] : 'Consumer Tech') as Sector;
}

/**
 * Assign tier 1/2/3 based on background text.
 */
export function assignTier(text: string): { tier: Tier; rationale: string } {
  const lower = text.toLowerCase();

  // Tier 1: premier institution
  for (const inst of PREMIER_INSTITUTIONS) {
    if (lower.includes(inst.toLowerCase())) {
      return { tier: 1, rationale: `${inst} alumni` };
    }
  }

  // Tier 1: top company
  for (const company of TOP_COMPANIES) {
    if (lower.includes(company.toLowerCase())) {
      return { tier: 1, rationale: `Ex-${company}` };
    }
  }

  // Tier 1: strong traction
  const tractionSignals = ['series a', 'series b', 'million users', 'revenue', 'arr', 'unicorn'];
  for (const signal of tractionSignals) {
    if (lower.includes(signal)) {
      return { tier: 1, rationale: `Strong traction (${signal})` };
    }
  }

  // Tier 2: some funding/signals
  const tier2Signals = ['raised', 'seed', 'pre-seed', 'backed by', 'accelerator', 'yc', 'antler', 'surge'];
  for (const signal of tier2Signals) {
    if (lower.includes(signal)) {
      return { tier: 2, rationale: 'Some funding/accelerator signals' };
    }
  }

  // Tier 3: default
  return { tier: 3, rationale: 'Early stage, limited public info' };
}

/**
 * Enrich a partial startup record into the full schema.
 * Optionally fetches LinkedIn URL if missing (slow - does a Google search).
 */
export async function enrichStartup(
  raw: Partial<Startup> & { snippet?: string },
  fetchLinkedIn = false
): Promise<Startup> {
  const founderName = raw.founder_name ?? 'Unknown';
  let startupName = raw.startup_name ?? 'Stealth Startup';

  // For LinkedIn-profile-only records: derive a unique startup_name from the
  // URL slug so the D1 unique constraint (founder_name, startup_name) never
  // collapses multiple distinct profiles into one row.
  const linkedinRaw = raw.linkedin_url ?? null;
  if (startupName === 'Stealth Startup' && linkedinRaw?.includes('linkedin.com/in/')) {
    const slug = linkedinRaw.split('/in/')[1]?.replace(/\/$/, '').split('?')[0] ?? '';
    if (slug) startupName = `[Profile] ${slug}`;
  }

  // LinkedIn
  let linkedinUrl = raw.linkedin_url ?? null;
  if (!linkedinUrl && fetchLinkedIn && founderName !== 'Unknown') {
    linkedinUrl = await findLinkedInUrl(founderName, startupName);
  }

  // Sector
  const descriptionText = [raw.one_liner, raw.snippet, startupName].filter(Boolean).join(' ');
  const sector = raw.sector ?? classifySector(descriptionText);

  // Tier
  const backgroundText = [raw.tier_rationale, raw.one_liner, raw.snippet].filter(Boolean).join(' ');
  const { tier, rationale } = raw.tier
    ? { tier: raw.tier, rationale: raw.tier_rationale ?? '' }
    : assignTier(backgroundText);

  return {
    founder_name: founderName,
    startup_name: startupName,
    linkedin_url: linkedinUrl,
    website: raw.website ?? null,
    sector,
    one_liner: (raw.one_liner ?? raw.snippet ?? '').slice(0, 120),
    tier,
    tier_rationale: (rationale || raw.tier_rationale || '').slice(0, 100),
    source: raw.source ?? 'Enricher',
    founded_year: raw.founded_year ?? 2024,
  };
}

// ── Funding stage extraction ──

const FUNDING_STAGE_MAP: Array<[RegExp, string]> = [
  // Actively seeking - highest priority for VCs
  [/looking for (investors|funding|investment)|seeking (investment|funding|pre.?seed)|open to (investment|funding)|raising (pre.?seed|angel)|fundraising|pitch(ing)? (to )?(investor|vc|fund)/i, 'Seeking Pre-Seed'],
  // Unfunded
  [/\bunfunded\b|bootstrapped|self.?funded|no (external )?funding|zero funding/i, 'Unfunded'],
  // Pre-seed
  [/pre.?seed/i, 'Pre-Seed'],
  // Angel
  [/angel (round|funded|backed|investment)/i, 'Angel'],
  // Seed
  [/\bseed (round|funded|stage|funding)\b|\braised seed\b/i, 'Seed'],
  // Series A+
  [/series a/i, 'Series A'],
  [/series b/i, 'Series B'],
  [/series c/i, 'Series C'],
];

export function extractFundingStage(text: string): string | null {
  for (const [pattern, stage] of FUNDING_STAGE_MAP) {
    if (pattern.test(text)) return stage;
  }
  return null;
}

// ── City extraction ──

const CITY_MAP: Array<[RegExp, string]> = [
  [/bengaluru|bangalore/i, 'Bengaluru'],
  [/\bnew delhi\b|gurugram|gurgaon|\bnoida\b|faridabad|\bncr\b/i, 'Delhi NCR'],
  [/\bdelhi\b/i, 'Delhi NCR'],
  [/navi mumbai|thane|\bmumbai\b|\bbombay\b/i, 'Mumbai'],
  [/hyderabad/i, 'Hyderabad'],
  [/chennai|madras/i, 'Chennai'],
  [/\bpune\b/i, 'Pune'],
  [/ahmedabad/i, 'Ahmedabad'],
  [/kolkata|calcutta/i, 'Kolkata'],
  [/\bkochi\b|cochin/i, 'Kochi'],
  [/chandigarh/i, 'Chandigarh'],
  [/\bindore\b/i, 'Indore'],
  [/coimbatore/i, 'Coimbatore'],
  [/\bjaipur\b/i, 'Jaipur'],
  [/\bsurat\b/i, 'Surat'],
  [/\bnagpur\b/i, 'Nagpur'],
  [/\bbhopal\b/i, 'Bhopal'],
  [/\bvisakhapatnam\b|vizag/i, 'Visakhapatnam'],
];

export function extractCity(text: string): string | null {
  for (const [pattern, city] of CITY_MAP) {
    if (pattern.test(text)) return city;
  }
  return null;
}

// ── Raw result → Startup parsing ──

interface RawHit {
  url: string;
  title: string;
  snippet: string;
  source_type: string;
}

function extractYear(text: string): number {
  const m = text.match(/\b(202[0-9])\b/);
  return m ? parseInt(m[1]) : 2024;
}

export function parseRawResult(raw: RawHit): Partial<Startup> & { snippet: string } {
  const text = `${raw.title} ${raw.snippet}`;
  const sector = classifySector(text);
  const { tier, rationale } = assignTier(text);

  let founderName = 'Unknown';
  let startupName = 'Stealth Startup';
  let linkedinUrl: string | null = null;
  let website: string | null = null;

  if (raw.source_type.startsWith('linkedin:') && raw.url.includes('linkedin.com/in/')) {
    linkedinUrl = raw.url.split('?')[0];

    // Name extraction - handles many LinkedIn title formats:
    // "Rahul Sharma - Co-Founder at XYZ | LinkedIn"
    // "Rahul Sharma · Building in AI | LinkedIn"
    // "Rahul Sharma | Founder, XYZ"
    // "Rahul Sharma, CEO at XYZ"
    const nameMatch = raw.title.match(/^([A-Z][a-zA-Z]+(?: [A-Z][a-zA-Z]+){1,4})(?:\s*[-–·|,]|\s+at\s|\s+\|)/);
    if (nameMatch) founderName = nameMatch[1].trim();

    // If still unknown, try extracting from URL slug
    if (founderName === 'Unknown') {
      const slug = linkedinUrl.split('/in/')[1]?.replace(/-\d+$/, '').replace(/-/g, ' ');
      if (slug && slug.split(' ').length >= 2) {
        founderName = slug.split(' ').slice(0, 3).map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
      }
    }

    // Startup name - title first, then snippet
    const atTitleMatch = raw.title.match(/\bat\s+([A-Z][^|–\-,\.·]{2,40})/i)
                      ?? raw.title.match(/,\s*([A-Z][^|–\-,\.·]{2,40})\s*(?:\||$)/);
    if (atTitleMatch) startupName = atTitleMatch[1].trim();

    if (startupName === 'Stealth Startup') {
      const snippetMatch = raw.snippet.match(
        /(?:building|founded|at|CEO of|founder of|co-founder of|working on|launched)\s+([A-Z][A-Za-z0-9][^,\.·|\n]{2,35})/i
      );
      if (snippetMatch) startupName = snippetMatch[1].trim();
    }

  } else if (raw.source_type.startsWith('twitter:')) {
    // "Rahul Sharma (@handle) on X" or "Rahul Sharma / X"
    const nameMatch = raw.title.match(/^([A-Z][a-zA-Z]+(?: [A-Z][a-zA-Z]+){0,3})(?:\s*\(@|\s*\/|\s+on\s)/i)
                   ?? raw.title.match(/^([^(@/|·\n]{4,40})(?:\s*[@(/|])/);
    if (nameMatch) founderName = nameMatch[1].trim();

    const startupMatch = raw.snippet.match(
      /(?:building|founded|launched|CEO of|founder of|co-founder of|working on)\s+([A-Z][A-Za-z0-9][^,\.|\n]{2,35})/i
    );
    if (startupMatch) startupName = startupMatch[1].trim();

  } else if (raw.source_type.startsWith('crunchbase:') && raw.url.includes('crunchbase.com/organization/')) {
    // "StartupName - Crunchbase Company Profile..."
    const nameMatch = raw.title.match(/^([^–\-|]+?)(?:\s*[-–|])/);
    if (nameMatch) startupName = nameMatch[1].trim();
    // Fall back to org slug if title parse failed
    if (!nameMatch) {
      const slug = raw.url.split('/organization/')[1]?.split('/')[0]?.replace(/-/g, ' ');
      if (slug) startupName = slug.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
    }
    website = raw.url.split('?')[0];

  } else if (raw.source_type.startsWith('producthunt:')) {
    // "ProductName - tagline | Product Hunt"
    const nameMatch = raw.title.match(/^([^–\-|]+?)(?:\s*[-–|])/);
    if (nameMatch) startupName = nameMatch[1].trim();
    website = raw.url.split('?')[0];

  } else if (raw.source_type.startsWith('wellfound:')) {
    // "StartupName - Wellfound" or "StartupName | Overview, Team..."
    const nameMatch = raw.title.match(/^([^–\-|]+?)(?:\s*[-–|])/);
    if (nameMatch) startupName = nameMatch[1].trim();
    website = raw.url.split('?')[0];
    // Wellfound snippets often have "Funding: Pre-Seed" or "Funding: Unfunded"
    const fundingMatch = raw.snippet.match(/funding[:\s]+([A-Za-z\s-]+?)(?:\s*[·|,\n]|$)/i);
    if (fundingMatch) {
      // override funding_stage will be picked up by extractFundingStage on the full text
    }

  } else if (raw.source_type.startsWith('newsmedia:')) {
    // Inc42, YourStory, ET, etc. - startup name usually in title before " raises" or " launches"
    const raisesMatch = raw.title.match(/^([^–\-|]+?)(?:\s+raises|\s+gets|\s+secures|\s+closes|\s+launches)/i);
    const generalMatch = raw.title.match(/^([^–\-|:]{3,50})(?:\s*[-–|:])/);
    const m = raisesMatch ?? generalMatch;
    if (m) startupName = m[1].trim();

    // Extract founder name from snippet: "founded by Rahul Sharma" or "Rahul Sharma, founder"
    const founderMatch = raw.snippet.match(
      /(?:founded by|co-founded by|started by)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})/i
    ) ?? raw.snippet.match(/([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}),?\s+(?:founder|co-founder|CEO)/i);
    if (founderMatch) founderName = founderMatch[1].trim();

  } else if (raw.source_type.startsWith('accelerator:')) {
    const nameMatch = raw.title.match(/^([^–\-|:]{3,50})(?:\s*[-–|:])/);
    if (nameMatch) startupName = nameMatch[1].trim();

  } else if (raw.source_type.startsWith('mca:')) {
    // "COMPANY NAME PRIVATE LIMITED - CIN..." → strip "PRIVATE LIMITED"
    const nameMatch = raw.title.match(/^([^–\-|]+?)(?:\s+PRIVATE LIMITED|\s*[-–|])/i);
    if (nameMatch) startupName = nameMatch[1].trim();
    website = raw.url.split('?')[0];

  } else if (raw.source_type.startsWith('reddit:')) {
    // Reddit posts: title is the post title, snippet is body preview
    // Pattern: "Show r/IndiaStartups: StartupName - ..." or free-form
    const showMatch = raw.title.match(/(?:show\s+\S+:\s*|launched\s+|we built\s+|check out\s+)([A-Z][A-Za-z0-9][^,\.|\n]{2,40})/i);
    const generalMatch = raw.title.match(/^([A-Z][A-Za-z0-9][^–\-|:,\n]{2,40})(?:\s*[-–|:])/);
    const m = showMatch ?? generalMatch;
    if (m) startupName = m[1].trim();

    // Founder name from "I'm [Name]" or "My name is [Name]"
    const nameMatch = raw.snippet.match(/(?:I(?:'m| am)\s+|my name is\s+)([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})/i);
    if (nameMatch) founderName = nameMatch[1].trim();

    // Startup from snippet if title parse failed
    if (startupName === 'Stealth Startup') {
      const snippetMatch = raw.snippet.match(
        /(?:building|launched|founded|working on|our startup|our product|our app)\s+([A-Z][A-Za-z0-9][^,\.|\n]{2,35})/i
      );
      if (snippetMatch) startupName = snippetMatch[1].trim();
    }

  } else if (
    raw.source_type.startsWith('inc42:') ||

    raw.source_type.startsWith('yourstory:') ||
    raw.source_type.startsWith('nasscom:') ||
    raw.source_type.startsWith('startup_india:') ||
    raw.source_type.startsWith('google_news:') ||
    raw.source_type.startsWith('sebi:') ||
    raw.source_type.startsWith('angellist:') ||
    raw.source_type.startsWith('gust:')
  ) {
    // News / directory sources: parse like newsmedia
    const raisesMatch = raw.title.match(/^([^–\-|]+?)(?:\s+raises|\s+gets|\s+secures|\s+closes|\s+launches|\s+debuts)/i);
    const generalMatch = raw.title.match(/^([^–\-|:]{3,50})(?:\s*[-–|:])/);
    const m = raisesMatch ?? generalMatch;
    if (m) startupName = m[1].trim();

    const founderMatch = raw.snippet.match(
      /(?:founded by|co-founded by|started by)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})/i
    ) ?? raw.snippet.match(/([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}),?\s+(?:founder|co-founder|CEO)/i);
    if (founderMatch) founderName = founderMatch[1].trim();
    website = raw.url.split('?')[0];

  } else if (raw.source_type.startsWith('hackernews:')) {
    // "Show HN: StartupName – tagline" or "Ask HN: ..."
    const showMatch = raw.title.match(/^(?:Show|Ask)\s+HN:\s*([^–\-|,]{3,50})(?:\s*[-–|,]|$)/i);
    const generalMatch = raw.title.match(/^([^–\-|:]{3,50})(?:\s*[-–|:])/);
    const m = showMatch ?? generalMatch;
    if (m) startupName = m[1].trim();

    const founderMatch = raw.snippet.match(
      /(?:founded by|co-founded by|I(?:'m| am) the founder|built by)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})/i
    );
    if (founderMatch) founderName = founderMatch[1].trim();

  } else if (raw.source_type.startsWith('vc_portfolio:')) {
    // "StartupName | Sequoia India" or "StartupName - Portfolio"
    const nameMatch = raw.title.match(/^([^–\-|]{3,50})(?:\s*[-–|])/);
    if (nameMatch) startupName = nameMatch[1].trim();
    website = raw.url.split('?')[0];

    const founderMatch = raw.snippet.match(
      /(?:founded by|co-founded by)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})/i
    );
    if (founderMatch) founderName = founderMatch[1].trim();
  }

  return {
    founder_name: founderName,
    startup_name: startupName,
    linkedin_url: linkedinUrl,
    website,
    sector,
    one_liner: raw.snippet.slice(0, 120),
    tier,
    tier_rationale: rationale,
    source: raw.source_type,
    founded_year: extractYear(text),
    city: extractCity(text),
    funding_stage: extractFundingStage(text),
    snippet: raw.snippet,
  };
}

export function processRawToStartups(rawHits: RawHit[]): Startup[] {
  const startups: Startup[] = [];

  // Deduplicate LinkedIn URLs so every unique profile is kept even when
  // both name fields remain unresolved (e.g. slug-only records).
  const seenLinkedin = new Set<string>();
  const seenNames = new Set<string>();

  for (const raw of rawHits) {
    const p = parseRawResult(raw);

    // Drop only if truly empty - no name AND no startup AND no LinkedIn URL
    if (p.founder_name === 'Unknown' && p.startup_name === 'Stealth Startup' && !p.linkedin_url) continue;

    // Deduplicate
    const nameKey = p.startup_name?.toLowerCase().trim() ?? '';
    const linkedinKey = p.linkedin_url?.toLowerCase().replace(/\/$/, '') ?? '';
    const isPlaceholder = nameKey === 'stealth startup' || nameKey === '';

    if (!isPlaceholder) {
      if (seenNames.has(nameKey)) continue;
      seenNames.add(nameKey);
    } else {
      // profile-only record - dedupe by LinkedIn URL
      if (!linkedinKey || seenLinkedin.has(linkedinKey)) continue;
    }
    if (linkedinKey) seenLinkedin.add(linkedinKey);

    startups.push({
      founder_name: p.founder_name!,
      startup_name: p.startup_name!,
      linkedin_url: p.linkedin_url ?? null,
      website: p.website ?? null,
      sector: p.sector!,
      one_liner: p.one_liner ?? '',
      tier: p.tier!,
      tier_rationale: p.tier_rationale ?? '',
      source: p.source!,
      founded_year: p.founded_year ?? 2024,
      city: p.city ?? null,
      funding_stage: p.funding_stage ?? null,
    });
  }
  return startups;
}
