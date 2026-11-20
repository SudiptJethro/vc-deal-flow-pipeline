/**
 * Seed script - reads ../data/startups.json and generates seed.sql for D1.
 * Run: npx tsx seed.ts
 * Then: npm run db:seed (or db:seed:local)
 */

import { readFileSync, writeFileSync } from 'fs';
import { join } from 'path';

const dataPath = join(__dirname, '..', 'data', 'startups.json');
const outputPath = join(__dirname, 'seed.sql');

interface Startup {
  founder_name: string;
  startup_name: string;
  linkedin_url: string | null;
  website: string | null;
  sector: string;
  one_liner: string;
  tier: number;
  tier_rationale: string;
  source: string;
  founded_year: number;
}

const raw = readFileSync(dataPath, 'utf-8');
const startups: Startup[] = JSON.parse(raw);

const esc = (s: string | null): string => {
  if (s === null || s === undefined) return 'NULL';
  return `'${s.replace(/'/g, "''")}'`;
};

const lines = startups.map(s =>
  `INSERT OR IGNORE INTO startups (founder_name, startup_name, linkedin_url, website, sector, one_liner, tier, tier_rationale, source, founded_year)
VALUES (${esc(s.founder_name)}, ${esc(s.startup_name)}, ${esc(s.linkedin_url)}, ${esc(s.website)}, ${esc(s.sector)}, ${esc(s.one_liner)}, ${s.tier}, ${esc(s.tier_rationale)}, ${esc(s.source)}, ${s.founded_year});`
);

const sql = `-- Auto-generated seed data from startups.json
-- Run: npm run db:seed (remote) or npm run db:seed:local

${lines.join('\n\n')}
`;

writeFileSync(outputPath, sql, 'utf-8');
console.log(`Generated ${outputPath} with ${startups.length} INSERT statements`);
