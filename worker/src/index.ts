// ============================================
// Deal Flow Pipeline - Cloudflare Worker
// API endpoints + Cron-triggered scraping + KV caching
// ============================================

import puppeteer from '@cloudflare/puppeteer';
import type { Env, Startup, ApiResponse } from './types';
import {
  getAllStartups, getStartupsFiltered, getStartupById,
  upsertStartup, bulkUpsertStartups, deleteStartup,
  getStats, getScrapeRuns,
} from './db';
// Scrapers are intentionally NOT imported here - they run in the Python pipeline
// via GitHub Actions, not inside the Worker. See scripts/run_all.py.

// KV TTLs
const KV_TTL_API  = 60 * 5;   // 5 min for /api/startups responses
const KV_TTL_STATS = 60 * 10; // 10 min for /api/stats

// ── Helpers ──

function corsHeaders(env: Env): Record<string, string> {
  return {
    'Access-Control-Allow-Origin': env.CORS_ORIGIN || '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
  };
}

/**
 * Check Bearer token for write endpoints.
 * If PIPELINE_SECRET is not set, write endpoints are open (dev mode).
 */
function isAuthorized(request: Request, env: Env): boolean {
  if (!env.PIPELINE_SECRET) return true; // no secret configured = open
  const auth = request.headers.get('Authorization') ?? '';
  return auth === `Bearer ${env.PIPELINE_SECRET}`;
}

function json<T>(data: ApiResponse<T>, status: number, env: Env): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json', ...corsHeaders(env) },
  });
}

async function cachedJson<T>(
  key: string,
  ttl: number,
  env: Env,
  fetch: () => Promise<T>
): Promise<Response> {
  const cached = await env.KV.get(key);
  if (cached) {
    return new Response(cached, {
      headers: { 'Content-Type': 'application/json', 'X-Cache': 'HIT', ...corsHeaders(env) },
    });
  }
  const data = await fetch();
  const body = JSON.stringify({ ok: true, data });
  await env.KV.put(key, body, { expirationTtl: ttl });
  return new Response(body, {
    headers: { 'Content-Type': 'application/json', 'X-Cache': 'MISS', ...corsHeaders(env) },
  });
}

// ── Router ──

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    const path = url.pathname;
    const method = request.method;

    if (method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: corsHeaders(env) });
    }

    try {
      // ── GET /api/startups ──
      if (method === 'GET' && path === '/api/startups') {
        const sector = url.searchParams.get('sector') ?? undefined;
        const tier   = url.searchParams.get('tier') ? Number(url.searchParams.get('tier')) : undefined;
        const source = url.searchParams.get('source') ?? undefined;
        const search = url.searchParams.get('search') ?? undefined;
        const year   = url.searchParams.get('year') ? Number(url.searchParams.get('year')) : undefined;
        const city          = url.searchParams.get('city') ?? undefined;
        const funding_stage = url.searchParams.get('funding_stage') ?? undefined;

        const cacheKey = `api:startups:${sector ?? ''}:${tier ?? ''}:${source ?? ''}:${search ?? ''}:${year ?? ''}:${city ?? ''}:${funding_stage ?? ''}`;
        return cachedJson(cacheKey, KV_TTL_API, env, async () => {
          const startups = await getStartupsFiltered(env.DB, { sector: sector as any, tier: tier as any, source, search, year, city, funding_stage });
          return startups;
        });
      }

      // ── GET /api/startups/:id ──
      if (method === 'GET' && path.match(/^\/api\/startups\/\d+$/)) {
        const id = Number(path.split('/').pop());
        const startup = await getStartupById(env.DB, id);
        if (!startup) return json({ ok: false, error: 'Not found' }, 404, env);
        return json({ ok: true, data: startup }, 200, env);
      }

      // ── POST /api/startups ──
      if (method === 'POST' && path === '/api/startups') {
        if (!isAuthorized(request, env)) return json({ ok: false, error: 'Unauthorized' }, 401, env);
        const body = await request.json<Startup>();
        await upsertStartup(env.DB, body);
        await env.KV.delete('api:stats');
        return json({ ok: true }, 201, env);
      }

      // ── POST /api/startups/bulk ──
      if (method === 'POST' && path === '/api/startups/bulk') {
        if (!isAuthorized(request, env)) return json({ ok: false, error: 'Unauthorized' }, 401, env);
        const body = await request.json<Startup[]>();
        const count = await bulkUpsertStartups(env.DB, body);
        await env.KV.delete('api:stats');
        return json({ ok: true, meta: { upserted: count } }, 201, env);
      }

      // ── DELETE /api/startups/:id ──
      if (method === 'DELETE' && path.match(/^\/api\/startups\/\d+$/)) {
        if (!isAuthorized(request, env)) return json({ ok: false, error: 'Unauthorized' }, 401, env);
        const id = Number(path.split('/').pop());
        await deleteStartup(env.DB, id);
        await env.KV.delete('api:stats');
        return json({ ok: true }, 200, env);
      }

      // ── GET /api/stats ──
      if (method === 'GET' && path === '/api/stats') {
        return cachedJson('api:stats', KV_TTL_STATS, env, () => getStats(env.DB));
      }

      // ── GET /api/scrape-runs ──
      if (method === 'GET' && path === '/api/scrape-runs') {
        const runs = await getScrapeRuns(env.DB);
        return json({ ok: true, data: runs }, 200, env);
      }

      // ── POST /api/render ──
      // Renders a URL using Cloudflare Browser Rendering (headless Chrome).
      // Called by the Python scraping pipeline to fetch JS-heavy portfolio pages.
      // Body: { "url": "https://...", "waitMs": 2000 }
      // Returns: { ok: true, data: { html: "..." } }
      if (method === 'POST' && path === '/api/render') {
        if (!isAuthorized(request, env)) return json({ ok: false, error: 'Unauthorized' }, 401, env);

        const { url: targetUrl, waitMs = 2000 } = await request.json<{ url: string; waitMs?: number }>();
        if (!targetUrl) return json({ ok: false, error: 'Missing url' }, 400, env);

        let html = '';
        try {
          const browser = await puppeteer.launch(env.BROWSER);
          const page = await browser.newPage();
          // Block heavy assets to speed up rendering
          await page.setRequestInterception(true);
          page.on('request', (req) => {
            const type = req.resourceType();
            if (['image', 'media', 'font', 'stylesheet'].includes(type)) {
              req.abort();
            } else {
              req.continue();
            }
          });
          try {
            // networkidle2 instead of networkidle0: SPAs never reach networkidle0
            // due to background polling. networkidle2 fires once the main content loads.
            await page.goto(targetUrl, { waitUntil: 'networkidle2', timeout: 20000 });
          } catch {
            // Navigation timeout is non-fatal - partial content is still useful
            console.warn(`[/api/render] navigation timeout for ${targetUrl}, using partial content`);
          }
          if (waitMs > 0) await new Promise(r => setTimeout(r, waitMs));
          html = await page.content();
          await browser.close();
        } catch (err: any) {
          return json({ ok: false, error: `Browser render failed: ${err.message}` }, 500, env);
        }

        return json({ ok: true, data: { html } }, 200, env);
      }

      // ── GET /api/export/csv ──
      if (method === 'GET' && path === '/api/export/csv') {
        const startups = await getAllStartups(env.DB);
        return new Response(startupsToCsv(startups), {
          headers: {
            'Content-Type': 'text/csv',
            'Content-Disposition': 'attachment; filename="deal_flow_pipeline.csv"',
            ...corsHeaders(env),
          },
        });
      }

      // ── GET /api/export/json ──
      if (method === 'GET' && path === '/api/export/json') {
        const startups = await getAllStartups(env.DB);
        return new Response(JSON.stringify(startups, null, 2), {
          headers: {
            'Content-Type': 'application/json',
            'Content-Disposition': 'attachment; filename="deal_flow_pipeline.json"',
            ...corsHeaders(env),
          },
        });
      }

      // ── Health check ──
      if (method === 'GET' && (path === '/' || path === '/health')) {
        return json({ ok: true, data: { status: 'running', version: '1.0.0' } }, 200, env);
      }

      return json({ ok: false, error: 'Not found' }, 404, env);
    } catch (err: any) {
      console.error('Worker error:', err);
      return json({ ok: false, error: err.message ?? 'Internal error' }, 500, env);
    }
  },

  // Cron fires every 6 hours but scraping is intentionally NOT done here.
  // Cloudflare Workers have a hard 30-second wall-clock limit per invocation,
  // which is far too short to complete dozens of search queries with rate-limit
  // delays. Scraping is handled by the Python pipeline running in GitHub Actions,
  // which uploads results via POST /api/startups/bulk.
  //
  // This handler just logs a heartbeat so you can confirm the cron is running.
  async scheduled(_event: ScheduledEvent, env: Env, _ctx: ExecutionContext): Promise<void> {
    console.log(`[Cron] Heartbeat at ${new Date().toISOString()} - scraping handled by GitHub Actions`);
  },
};

// ── CSV Export ──

function startupsToCsv(startups: Startup[]): string {
  const headers = ['#', 'Founder', 'Startup', 'Sector', 'One-Liner', 'Tier', 'Tier Rationale', 'LinkedIn', 'Website', 'Source', 'Founded'];
  const escape = (s: string | null | undefined): string => {
    if (!s) return '';
    return s.includes(',') || s.includes('"') || s.includes('\n') ? `"${s.replace(/"/g, '""')}"` : s;
  };
  const rows = startups.map((s, i) =>
    [i + 1, escape(s.founder_name), escape(s.startup_name), escape(s.sector),
     escape(s.one_liner), s.tier, escape(s.tier_rationale),
     s.linkedin_url ?? '', s.website ?? '', escape(s.source), s.founded_year].join(',')
  );
  return [headers.join(','), ...rows].join('\n');
}
