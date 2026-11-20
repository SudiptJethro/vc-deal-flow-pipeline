// ============================================
// Deal Flow Pipeline - D1 Database Layer
// ============================================

import type { Startup, ScrapeRun, RawResult, Sector, Tier } from './types';

// ── Startups CRUD ──

export async function getAllStartups(db: D1Database): Promise<Startup[]> {
  const { results } = await db
    .prepare('SELECT * FROM startups ORDER BY tier ASC, founder_name ASC')
    .all<Startup>();
  return results;
}

export async function getStartupsFiltered(
  db: D1Database,
  filters: { sector?: Sector; tier?: Tier; source?: string; search?: string; year?: number; city?: string; funding_stage?: string }
): Promise<Startup[]> {
  const clauses: string[] = [];
  const params: unknown[] = [];

  if (filters.sector) {
    clauses.push('sector = ?');
    params.push(filters.sector);
  }
  if (filters.tier) {
    clauses.push('tier = ?');
    params.push(filters.tier);
  }
  if (filters.source) {
    clauses.push('source = ?');
    params.push(filters.source);
  }
  if (filters.year) {
    clauses.push('founded_year = ?');
    params.push(filters.year);
  }
  if (filters.city) {
    clauses.push('city = ?');
    params.push(filters.city);
  }
  if (filters.funding_stage) {
    clauses.push('funding_stage = ?');
    params.push(filters.funding_stage);
  }
  if (filters.search) {
    clauses.push(
      "(founder_name LIKE ? OR startup_name LIKE ? OR one_liner LIKE ? OR source LIKE ? OR city LIKE ?)"
    );
    const like = `%${filters.search}%`;
    params.push(like, like, like, like, like);
  }

  const where = clauses.length ? `WHERE ${clauses.join(' AND ')}` : '';
  const sql = `SELECT * FROM startups ${where} ORDER BY tier ASC, founder_name ASC`;

  const { results } = await db.prepare(sql).bind(...params).all<Startup>();
  return results;
}

export async function getStartupById(db: D1Database, id: number): Promise<Startup | null> {
  return db.prepare('SELECT * FROM startups WHERE id = ?').bind(id).first<Startup>();
}

const UPSERT_FIELDS = `
  founder_name, startup_name, linkedin_url, website, sector, one_liner,
  tier, tier_rationale, source, founded_year, city, funding_stage
`;
const UPSERT_VALUES = `?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?`;
const UPSERT_SET = `
  linkedin_url   = COALESCE(excluded.linkedin_url, startups.linkedin_url),
  website        = COALESCE(excluded.website, startups.website),
  sector         = excluded.sector,
  one_liner      = excluded.one_liner,
  tier           = excluded.tier,
  tier_rationale = excluded.tier_rationale,
  source         = excluded.source,
  founded_year   = excluded.founded_year,
  city           = COALESCE(excluded.city, startups.city),
  funding_stage  = COALESCE(excluded.funding_stage, startups.funding_stage),
  updated_at     = datetime('now')
`;

export async function upsertStartup(db: D1Database, s: Startup): Promise<void> {
  const params = [
    s.founder_name, s.startup_name, s.linkedin_url ?? null, s.website ?? null,
    s.sector, s.one_liner, s.tier, s.tier_rationale, s.source, s.founded_year,
    s.city ?? null, s.funding_stage ?? null,
  ];

  // Try name-based conflict first; if the record has a LinkedIn URL and is a
  // profile-only entry (startup_name starts with "[Profile]"), the unique index
  // on linkedin_url handles deduplication instead.
  await db
    .prepare(
      `INSERT INTO startups (${UPSERT_FIELDS}) VALUES (${UPSERT_VALUES})
       ON CONFLICT(founder_name, startup_name) DO UPDATE SET ${UPSERT_SET}`
    )
    .bind(...params)
    .run()
    .catch(async (err: Error) => {
      // If the linkedin_url partial-unique index fires, update that row instead
      if (s.linkedin_url && err.message?.includes('UNIQUE constraint failed')) {
        await db
          .prepare(
            `UPDATE startups SET
               founder_name   = COALESCE(?, founder_name),
               startup_name   = COALESCE(?, startup_name),
               website        = COALESCE(?, website),
               sector         = ?,
               one_liner      = ?,
               tier           = ?,
               tier_rationale = ?,
               source         = ?,
               founded_year   = ?,
               city           = COALESCE(?, city),
               funding_stage  = COALESCE(?, funding_stage),
               updated_at     = datetime('now')
             WHERE linkedin_url = ?`
          )
          .bind(
            s.founder_name, s.startup_name, s.website ?? null,
            s.sector, s.one_liner, s.tier, s.tier_rationale, s.source, s.founded_year,
            s.city ?? null, s.funding_stage ?? null, s.linkedin_url
          )
          .run();
      } else {
        throw err;
      }
    });
}

export async function bulkUpsertStartups(db: D1Database, startups: Startup[]): Promise<number> {
  let count = 0;
  const batchSize = 50; // D1 batch limit
  for (let i = 0; i < startups.length; i += batchSize) {
    const batch = startups.slice(i, i + batchSize);
    const stmts = batch.map(s =>
      db
        .prepare(
          `INSERT INTO startups (${UPSERT_FIELDS}) VALUES (${UPSERT_VALUES})
           ON CONFLICT(founder_name, startup_name) DO UPDATE SET ${UPSERT_SET}
           ON CONFLICT(linkedin_url)              DO UPDATE SET ${UPSERT_SET}`
        )
        .bind(
          s.founder_name, s.startup_name, s.linkedin_url ?? null, s.website ?? null,
          s.sector, s.one_liner, s.tier, s.tier_rationale, s.source, s.founded_year,
          s.city ?? null, s.funding_stage ?? null
        )
    );
    const results = await db.batch(stmts);
    count += results.filter(r => r.success).length;
  }
  return count;
}

export async function deleteStartup(db: D1Database, id: number): Promise<D1Result> {
  return db.prepare('DELETE FROM startups WHERE id = ?').bind(id).run();
}

// ── Stats ──

export async function getStats(db: D1Database) {
  const [total, bySector, byTier, withLinkedin, sources, years] = await db.batch([
    db.prepare('SELECT COUNT(*) as count FROM startups'),
    db.prepare('SELECT sector, COUNT(*) as count FROM startups GROUP BY sector'),
    db.prepare('SELECT tier, COUNT(*) as count FROM startups GROUP BY tier'),
    db.prepare("SELECT COUNT(*) as count FROM startups WHERE linkedin_url IS NOT NULL AND linkedin_url != ''"),
    db.prepare('SELECT DISTINCT source FROM startups ORDER BY source'),
    db.prepare('SELECT DISTINCT founded_year FROM startups ORDER BY founded_year DESC'),
  ]);

  return {
    total: (total.results[0] as any)?.count ?? 0,
    by_sector: Object.fromEntries((bySector.results as any[]).map(r => [r.sector, r.count])),
    by_tier: Object.fromEntries((byTier.results as any[]).map(r => [r.tier, r.count])),
    with_linkedin: (withLinkedin.results[0] as any)?.count ?? 0,
    sources: (sources.results as any[]).map(r => r.source),
    years: (years.results as any[]).map(r => r.founded_year),
  };
}

// ── Scrape Runs ──

export async function createScrapeRun(db: D1Database, scraperName: string): Promise<number> {
  const result = await db
    .prepare("INSERT INTO scrape_runs (scraper_name, status) VALUES (?, 'running')")
    .bind(scraperName)
    .run();
  return result.meta.last_row_id as number;
}

export async function completeScrapeRun(
  db: D1Database, runId: number, count: number, error?: string
): Promise<void> {
  await db
    .prepare(
      `UPDATE scrape_runs
       SET status = ?, results_count = ?, error_message = ?, completed_at = datetime('now')
       WHERE id = ?`
    )
    .bind(error ? 'failed' : 'completed', count, error ?? null, runId)
    .run();
}

export async function getScrapeRuns(db: D1Database, limit = 20): Promise<ScrapeRun[]> {
  const { results } = await db
    .prepare('SELECT * FROM scrape_runs ORDER BY started_at DESC LIMIT ?')
    .bind(limit)
    .all<ScrapeRun>();
  return results;
}

// ── Raw Results ──

export async function insertRawResults(
  db: D1Database, runId: number, results: { url: string; title: string; snippet: string; source_type: string }[]
): Promise<number> {
  if (!results.length) return 0;

  const batchSize = 50;
  let count = 0;
  for (let i = 0; i < results.length; i += batchSize) {
    const batch = results.slice(i, i + batchSize);
    const stmts = batch.map(r =>
      db
        .prepare('INSERT INTO raw_results (scrape_run_id, url, title, snippet, source_type) VALUES (?, ?, ?, ?, ?)')
        .bind(runId, r.url, r.title, r.snippet, r.source_type)
    );
    const res = await db.batch(stmts);
    count += res.filter(r => r.success).length;
  }
  return count;
}

export async function getUnprocessedResults(db: D1Database, limit = 50): Promise<RawResult[]> {
  const { results } = await db
    .prepare('SELECT * FROM raw_results WHERE processed = 0 ORDER BY created_at ASC LIMIT ?')
    .bind(limit)
    .all<RawResult>();
  return results;
}

export async function markProcessed(db: D1Database, ids: number[]): Promise<void> {
  if (!ids.length) return;
  const placeholders = ids.map(() => '?').join(',');
  await db.prepare(`UPDATE raw_results SET processed = 1 WHERE id IN (${placeholders})`).bind(...ids).run();
}

// ── Exclusions ──

export async function isExcluded(db: D1Database, startupName: string): Promise<boolean> {
  const row = await db
    .prepare('SELECT 1 FROM exclusions WHERE startup_name = ?')
    .bind(startupName)
    .first();
  return row !== null;
}

export async function addExclusion(db: D1Database, startupName: string): Promise<void> {
  await db
    .prepare('INSERT OR IGNORE INTO exclusions (startup_name) VALUES (?)')
    .bind(startupName)
    .run();
}
