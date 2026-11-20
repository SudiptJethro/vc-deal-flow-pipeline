// ============================================
// Deal Flow Pipeline - Types
// ============================================

export interface Env {
  DB: D1Database;
  KV: KVNamespace;
  BROWSER: Fetcher;            // Cloudflare Browser Rendering binding
  ENVIRONMENT: string;
  CORS_ORIGIN: string;
  SERPER_API_KEY?: string;
  PIPELINE_SECRET?: string;   // Bearer token required for write endpoints
}

export type Sector = 'Consumer AI' | 'Consumer Tech' | 'HealthTech';
export type Tier = 1 | 2 | 3;

export interface Startup {
  id?: number;
  founder_name: string;
  startup_name: string;
  linkedin_url: string | null;
  website: string | null;
  sector: Sector;
  one_liner: string;
  tier: Tier;
  tier_rationale: string;
  source: string;
  founded_year: number;
  city?: string | null;
  funding_stage?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface ScrapeRun {
  id?: number;
  scraper_name: string;
  status: 'running' | 'completed' | 'failed';
  results_count: number;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
}

export interface RawResult {
  id?: number;
  scrape_run_id: number;
  url: string;
  title: string;
  snippet: string;
  source_type: string;
  processed: number;
  created_at?: string;
}

export interface SearchResult {
  title: string;
  url: string;
  snippet: string;
}

export interface ApiResponse<T = unknown> {
  ok: boolean;
  data?: T;
  error?: string;
  meta?: Record<string, unknown>;
}
