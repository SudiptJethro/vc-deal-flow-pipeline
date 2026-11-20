-- ============================================
-- Deal Flow Pipeline - D1 Schema
-- Run: npm run db:migrate (remote) or db:migrate:local
-- ============================================

-- Main startups table
CREATE TABLE IF NOT EXISTS startups (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  founder_name  TEXT    NOT NULL,
  startup_name  TEXT    NOT NULL,
  linkedin_url  TEXT,
  website       TEXT,
  sector        TEXT    NOT NULL CHECK(sector IN ('Consumer AI', 'Consumer Tech', 'HealthTech')),
  one_liner     TEXT,
  tier          INTEGER NOT NULL CHECK(tier IN (1, 2, 3)),
  tier_rationale TEXT,
  source        TEXT,
  founded_year  INTEGER,
  city          TEXT,
  funding_stage TEXT,
  is_new        INTEGER DEFAULT 0,
  created_at    TEXT    DEFAULT (datetime('now')),
  updated_at    TEXT    DEFAULT (datetime('now'))
);

-- Unique constraint: one entry per founder+startup combo
CREATE UNIQUE INDEX IF NOT EXISTS idx_startups_founder_startup
  ON startups(founder_name, startup_name);

-- Unique constraint on LinkedIn URL (partial - only for non-null URLs)
-- Ensures LinkedIn-profile-only records are never collapsed into one row
CREATE UNIQUE INDEX IF NOT EXISTS idx_startups_linkedin_url
  ON startups(linkedin_url)
  WHERE linkedin_url IS NOT NULL AND linkedin_url != '';

-- Fast lookups
CREATE INDEX IF NOT EXISTS idx_startups_sector ON startups(sector);
CREATE INDEX IF NOT EXISTS idx_startups_tier   ON startups(tier);
CREATE INDEX IF NOT EXISTS idx_startups_year   ON startups(founded_year);
CREATE INDEX IF NOT EXISTS idx_startups_source ON startups(source);

-- Scrape run tracking
CREATE TABLE IF NOT EXISTS scrape_runs (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  scraper_name  TEXT    NOT NULL,
  status        TEXT    NOT NULL DEFAULT 'running' CHECK(status IN ('running', 'completed', 'failed')),
  results_count INTEGER DEFAULT 0,
  error_message TEXT,
  started_at    TEXT    DEFAULT (datetime('now')),
  completed_at  TEXT
);

-- Raw scraper results (before enrichment)
CREATE TABLE IF NOT EXISTS raw_results (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  scrape_run_id INTEGER REFERENCES scrape_runs(id),
  url           TEXT,
  title         TEXT,
  snippet       TEXT,
  source_type   TEXT    NOT NULL,
  processed     INTEGER DEFAULT 0,
  created_at    TEXT    DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_raw_processed ON raw_results(processed);

-- Excluded startups (already in your pipeline)
CREATE TABLE IF NOT EXISTS exclusions (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  startup_name  TEXT    NOT NULL UNIQUE
);

-- Add your own exclusions, e.g.:
-- INSERT OR IGNORE INTO exclusions (startup_name) VALUES ('Example Co');
