// ============================================
// DEAL FLOW PIPELINE - Dashboard Logic
// Loads from Cloudflare Worker API (D1) first,
// falls back to static data.js if offline/local.
// ============================================

(function () {
  'use strict';

  // ── Config ──
  // Set this to your deployed Worker URL (e.g. https://deal-flow-pipeline.<you>.workers.dev)
  // Leave empty string to skip API and use static data.js only.
  const API_BASE = '';

  // ── State ──
  let STARTUPS = [];          // master dataset (loaded from API or data.js)
  let currentView = 'table';
  let sortField = 'tier';
  let sortDir = 'asc';
  let filteredData = [];
  let apiConnected = false;
  let newOnlyActive = false;

  // D1 returns 1/0 integers; JSON returns true/false booleans - handle both
  const isNew = s => s.is_new === true || s.is_new === 1;

  // Shortlist: Set of unique keys (`startup_name||founder_name`).
  // Persisted to localStorage so selections survive page refreshes.
  const SHORTLIST_KEY = 'dealflow_shortlist_v1';
  let shortlist = new Set(JSON.parse(localStorage.getItem(SHORTLIST_KEY) || '[]'));

  function slKey(s) { return `${s.startup_name}||${s.founder_name}`; }
  function slStartup(key) {
    const [startup_name, founder_name] = key.split('||');
    return STARTUPS.find(s => s.startup_name === startup_name && s.founder_name === founder_name)
        ?? { startup_name, founder_name, sector: '', tier: '', funding_stage: '', city: '', linkedin_url: null, one_liner: '' };
  }

  function saveShortlist() {
    localStorage.setItem(SHORTLIST_KEY, JSON.stringify([...shortlist]));
  }

  function toggleShortlist(s) {
    const k = slKey(s);
    if (shortlist.has(k)) shortlist.delete(k); else shortlist.add(k);
    saveShortlist();
    updateShortlistUI();
  }

  function updateShortlistUI() {
    const count = shortlist.size;
    const badge = $('#shortlistBadge');
    const bar   = $('#shortlistBar');

    // Badge on header button
    badge.textContent = count;
    badge.classList.toggle('hidden', count === 0);

    // Floating bar
    if (count === 0) {
      bar.classList.add('hidden');
      document.body.classList.remove('shortlist-active');
    } else {
      bar.classList.remove('hidden');
      document.body.classList.add('shortlist-active');
    }

    // Count label
    $('#shortlistCount').textContent = count;

    // Chips
    const chips = $('#shortlistChips');
    chips.innerHTML = [...shortlist].map(k => {
      const name = k.split('||')[0];
      return `<span class="shortlist-chip">${esc(name)}<button class="shortlist-chip-remove" data-key="${esc(k)}" title="Remove">&#10005;</button></span>`;
    }).join('');

    // Re-apply selected class to visible rows/cards without full re-render
    document.querySelectorAll('tr[data-key]').forEach(tr => {
      tr.classList.toggle('row-selected', shortlist.has(tr.dataset.key));
    });
    document.querySelectorAll('.card[data-key]').forEach(card => {
      card.classList.toggle('card-selected', shortlist.has(card.dataset.key));
    });

    // Update drawer if open
    if (!$('#shortlistDrawer').classList.contains('hidden')) renderDrawer();
  }

  // ── DOM refs ──
  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => document.querySelectorAll(sel);

  const searchInput = $('#searchInput');
  const sectorFilter = $('#sectorFilter');
  const tierFilter = $('#tierFilter');
  const sourceFilter = $('#sourceFilter');
  const yearFilter = $('#yearFilter');
  const fundingFilter = $('#fundingFilter');
  const cityFilter = $('#cityFilter');
  const tableBody = $('#tableBody');
  const cardContainer = $('#cardContainer');
  const tableContainer = $('#tableContainer');

  // ── Boot ──
  document.addEventListener('DOMContentLoaded', async () => {
    await loadData();
    populateFilterOptions();
    updateStats(STARTUPS);
    applyFilters();
    bindEvents();
    const mode = apiConnected ? 'D1' : 'static';
    $('#lastUpdated').textContent =
      `Updated: ${new Date().toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })} (${mode})`;
  });

  // ── Data loading: API first, static fallback ──
  async function loadData() {
    if (API_BASE) {
      try {
        const resp = await fetch(`${API_BASE}/api/startups`);
        if (resp.ok) {
          const json = await resp.json();
          if (json.ok && Array.isArray(json.data) && json.data.length > 0) {
            STARTUPS = json.data;
            apiConnected = true;
            console.log(`Loaded ${STARTUPS.length} startups from Worker API (D1)`);
            return;
          }
        }
      } catch (e) {
        console.warn('Worker API unreachable, falling back to static data:', e.message);
      }
    }

    // Fallback: static data.js (STARTUPS_DATA global)
    if (typeof STARTUPS_DATA !== 'undefined' && STARTUPS_DATA.length) {
      STARTUPS = [...STARTUPS_DATA];
      console.log(`Loaded ${STARTUPS.length} startups from static data.js`);
    } else {
      STARTUPS = [];
      console.warn('No data source available');
    }
  }

  // ── Populate dynamic filter options ──

  // Canonical stage order for the funding filter dropdown
  const STAGE_ORDER = [
    'Seeking Pre-Seed',
    'Unfunded',
    'Pre-Seed',
    'Angel',
    'Seed',
    'Series A',
    'Series B+',
  ];

  function populateFilterOptions() {
    // Sources
    const sources = [...new Set(STARTUPS.map(s => s.source))].sort();
    sources.forEach(src => {
      const opt = document.createElement('option');
      opt.value = src;
      opt.textContent = src;
      sourceFilter.appendChild(opt);
    });

    // Years
    const years = [...new Set(STARTUPS.map(s => s.founded_year))].sort((a, b) => b - a);
    years.forEach(yr => {
      const opt = document.createElement('option');
      opt.value = yr;
      opt.textContent = yr;
      yearFilter.appendChild(opt);
    });

    // Funding stages - ordered by STAGE_ORDER, with count shown
    const stageCounts = {};
    STARTUPS.forEach(s => {
      const stage = s.funding_stage || 'Unknown';
      stageCounts[stage] = (stageCounts[stage] || 0) + 1;
    });

    // Known stages first (in canonical order), then any unexpected values
    const knownInData = STAGE_ORDER.filter(st => stageCounts[st]);
    const unknown = Object.keys(stageCounts).filter(st => !STAGE_ORDER.includes(st)).sort();

    [...knownInData, ...unknown].forEach(stage => {
      const opt = document.createElement('option');
      opt.value = stage;
      opt.textContent = `${stage}  (${stageCounts[stage]})`;
      fundingFilter.appendChild(opt);
    });
  }

  // ── Stats ──
  function updateStats(data) {
    $('#totalCount').textContent = data.length;
    $('#aiCount').textContent = data.filter(s => s.sector === 'Consumer AI').length;
    $('#techCount').textContent = data.filter(s => s.sector === 'Consumer Tech').length;
    $('#healthCount').textContent = data.filter(s => s.sector === 'HealthTech').length;
    $('#tier1Count').textContent = data.filter(s => s.tier === 1).length;
    $('#tier2Count').textContent = data.filter(s => s.tier === 2).length;
    $('#tier3Count').textContent = data.filter(s => s.tier === 3).length;
    $('#linkedinCount').textContent = data.filter(s => s.linkedin_url && !s.linkedin_url.includes('null')).length;
    // Always show new count from full STARTUPS (not filtered), so it's constant in the header
    $('#newCount').textContent = STARTUPS.filter(isNew).length;
  }

  // ── Filters ──
  function applyFilters() {
    const query = searchInput.value.toLowerCase().trim();
    const sector = sectorFilter.value;
    const tier = tierFilter.value;
    const source = sourceFilter.value;
    const year = yearFilter.value;
    const city    = cityFilter.value;
    const funding = fundingFilter.value;

    filteredData = STARTUPS.filter(s => {
      if (newOnlyActive && !isNew(s)) return false;
      if (sector && s.sector !== sector) return false;
      if (tier && s.tier !== parseInt(tier)) return false;
      if (source && s.source !== source) return false;
      if (year && s.founded_year !== parseInt(year)) return false;
      if (city && s.city !== city) return false;
      if (funding && s.funding_stage !== funding) return false;
      if (query) {
        const haystack = [s.founder_name, s.startup_name, s.one_liner, s.sector, s.source, s.tier_rationale, s.city]
          .join(' ').toLowerCase();
        return haystack.includes(query);
      }
      return true;
    });

    sortData();
    updateStats(filteredData);
    render();
  }

  // ── Sorting ──
  function sortData() {
    filteredData.sort((a, b) => {
      // NEW entries always float to the top, regardless of sort column
      const aN = isNew(a), bN = isNew(b);
      if (aN && !bN) return -1;
      if (!aN && bN) return 1;

      // Normal sort within each group
      let aVal = a[sortField];
      let bVal = b[sortField];
      if (typeof aVal === 'string') aVal = aVal.toLowerCase();
      if (typeof bVal === 'string') bVal = bVal.toLowerCase();
      if (aVal < bVal) return sortDir === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortDir === 'asc' ? 1 : -1;
      return 0;
    });
  }

  // ── Render ──
  function render() {
    if (currentView === 'table') renderTable();
    else renderCards();
  }

  function sectorBadgeClass(sector) {
    if (sector === 'Consumer AI') return 'badge-ai';
    if (sector === 'Consumer Tech') return 'badge-tech';
    return 'badge-health';
  }

  function fundingClass(stage) {
    if (!stage) return 'unknown';
    if (stage === 'Seeking Pre-Seed') return 'seeking';
    if (stage === 'Unfunded') return 'unfunded';
    if (stage === 'Pre-Seed') return 'preseed';
    if (stage === 'Angel') return 'angel';
    if (stage === 'Seed') return 'seed';
    if (stage === 'Series A') return 'series-a';
    return 'series-b';  // Series B+
  }

  function renderTable() {
    if (!filteredData.length) {
      tableBody.innerHTML = '<tr><td colspan="8"><div class="empty-state"><h3>No startups match your filters</h3><p>Try adjusting your search or filters</p></div></td></tr>';
      return;
    }

    tableBody.innerHTML = filteredData.map((s, i) => {
      const linkedinCell = s.linkedin_url
        ? `<a href="${s.linkedin_url}" target="_blank" rel="noopener" class="linkedin-link">Profile</a>`
        : '<span class="linkedin-link missing">--</span>';

      const websiteLink = s.website
        ? `<a href="${s.website}" target="_blank" rel="noopener" class="startup-link">&#8599;</a>`
        : '';

      const cityCell = s.city
        ? `<span class="city-tag">${esc(s.city)}</span>`
        : '<span class="city-tag unknown">-</span>';
      const fundingCell = s.funding_stage
        ? `<span class="funding-tag funding-${fundingClass(s.funding_stage)}">${esc(s.funding_stage)}</span>`
        : '<span class="city-tag unknown">-</span>';

      const k = slKey(s);
      const selected = shortlist.has(k);
      const newBadge = isNew(s) ? '<span class="badge-new">NEW</span>' : '';
      return `<tr class="clickable-row${selected ? ' row-selected' : ''}${isNew(s) ? ' row-new' : ''}" data-key="${esc(k)}">
        <td class="row-number">${selected ? '✓' : i + 1}</td>
        <td class="founder-name">${esc(s.founder_name)}</td>
        <td><div class="startup-name">${newBadge}${esc(s.startup_name)} ${websiteLink}</div></td>
        <td><span class="badge ${sectorBadgeClass(s.sector)}">${esc(s.sector)}</span></td>
        <td><div class="one-liner tooltip-container">${esc(s.one_liner)}<div class="tooltip">${esc(s.one_liner)}</div></div></td>
        <td><span class="tier tier-${s.tier}" title="${esc(s.tier_rationale)}">${s.tier}</span></td>
        <td>${fundingCell}</td>
        <td>${cityCell}</td>
        <td>${linkedinCell}</td>
        <td><span class="source-tag">${esc(s.source)}</span></td>
      </tr>`;
    }).join('');
  }

  function renderCards() {
    if (!filteredData.length) {
      cardContainer.innerHTML = '<div class="empty-state"><h3>No startups match your filters</h3><p>Try adjusting your search or filters</p></div>';
      return;
    }

    cardContainer.innerHTML = filteredData.map(s => {
      const linkedinBtn = s.linkedin_url
        ? `<a href="${s.linkedin_url}" target="_blank" rel="noopener" class="linkedin-link">LinkedIn</a>`
        : '<span class="linkedin-link missing">No LinkedIn</span>';

      const websiteBtn = s.website
        ? `<a href="${s.website}" target="_blank" rel="noopener" class="linkedin-link">Website</a>`
        : '';

      const k = slKey(s);
      const selected = shortlist.has(k);
      return `<div class="card clickable-card${selected ? ' card-selected' : ''}${isNew(s) ? ' card-new' : ''}" data-key="${esc(k)}">
        <div class="card-header">
          <div class="card-header-left">
            <div class="card-title">${isNew(s) ? '<span class="badge-new">NEW</span> ' : ''}${esc(s.startup_name)}</div>
            <div class="card-founder">${esc(s.founder_name)}</div>
          </div>
          <span class="tier tier-${s.tier}" title="${esc(s.tier_rationale)}">${s.tier}</span>
        </div>
        <div class="card-oneliner">${esc(s.one_liner)}</div>
        <div class="card-tags">
          <span class="badge ${sectorBadgeClass(s.sector)}">${esc(s.sector)}</span>
          ${s.funding_stage ? `<span class="funding-tag funding-${fundingClass(s.funding_stage)}">${esc(s.funding_stage)}</span>` : ''}
          ${s.city ? `<span class="city-tag">${esc(s.city)}</span>` : ''}
        </div>
        <div class="card-footer">
          <span class="source-tag">${esc(s.source)}</span>
          <div class="card-links">
            ${linkedinBtn}
            ${websiteBtn}
          </div>
        </div>
      </div>`;
    }).join('');
  }

  // ── Events ──
  function bindEvents() {
    searchInput.addEventListener('input', debounce(applyFilters, 200));
    sectorFilter.addEventListener('change', applyFilters);
    tierFilter.addEventListener('change', applyFilters);
    sourceFilter.addEventListener('change', applyFilters);
    yearFilter.addEventListener('change', applyFilters);
    fundingFilter.addEventListener('change', applyFilters);
    cityFilter.addEventListener('change', applyFilters);

    $('#newOnlyFilter').addEventListener('click', () => {
      newOnlyActive = !newOnlyActive;
      $('#newOnlyFilter').classList.toggle('btn-new-filter-active', newOnlyActive);
      applyFilters();
    });

    $('#clearFilters').addEventListener('click', () => {
      searchInput.value = '';
      sectorFilter.value = '';
      tierFilter.value = '';
      sourceFilter.value = '';
      yearFilter.value = '';
      fundingFilter.value = '';
      cityFilter.value = '';
      newOnlyActive = false;
      $('#newOnlyFilter').classList.remove('btn-new-filter-active');
      applyFilters();
    });

    $('#tableView').addEventListener('click', () => {
      currentView = 'table';
      tableContainer.classList.remove('hidden');
      cardContainer.classList.add('hidden');
      $('#tableView').classList.add('active');
      $('#cardView').classList.remove('active');
      render();
    });

    $('#cardView').addEventListener('click', () => {
      currentView = 'card';
      tableContainer.classList.add('hidden');
      cardContainer.classList.remove('hidden');
      $('#cardView').classList.add('active');
      $('#tableView').classList.remove('active');
      render();
    });

    $$('th.sortable').forEach(th => {
      th.addEventListener('click', () => {
        const field = th.dataset.sort;
        if (sortField === field) {
          sortDir = sortDir === 'asc' ? 'desc' : 'asc';
        } else {
          sortField = field;
          sortDir = 'asc';
        }
        $$('th.sortable').forEach(t => t.classList.remove('sorted-asc', 'sorted-desc'));
        th.classList.add(sortDir === 'asc' ? 'sorted-asc' : 'sorted-desc');
        sortData();
        render();
      });
    });

    $('#exportCsv').addEventListener('click', exportCsv);
    $('#exportJson').addEventListener('click', exportJson);
    $('#runScraper').addEventListener('click', runScraper);

    // ── Shortlist events ──

    // Click on table row → toggle shortlist (ignore clicks on links)
    tableBody.addEventListener('click', e => {
      if (e.target.closest('a')) return;
      const tr = e.target.closest('tr[data-key]');
      if (!tr) return;
      const k = tr.dataset.key;
      const s = filteredData.find(x => slKey(x) === k);
      if (s) { toggleShortlist(s); tr.classList.toggle('row-selected', shortlist.has(k)); }
      // Update row number cell
      const numCell = tr.querySelector('.row-number');
      if (numCell) numCell.textContent = shortlist.has(k) ? '✓' : tr.rowIndex;
    });

    // Click on card → toggle shortlist (ignore clicks on links)
    cardContainer.addEventListener('click', e => {
      if (e.target.closest('a')) return;
      const card = e.target.closest('.card[data-key]');
      if (!card) return;
      const k = card.dataset.key;
      const s = filteredData.find(x => slKey(x) === k);
      if (s) { toggleShortlist(s); card.classList.toggle('card-selected', shortlist.has(k)); }
    });

    // Chip remove buttons (delegated from bottom bar)
    $('#shortlistChips').addEventListener('click', e => {
      const btn = e.target.closest('.shortlist-chip-remove');
      if (!btn) return;
      shortlist.delete(btn.dataset.key);
      saveShortlist();
      updateShortlistUI();
      render(); // re-render to clear selected state
    });

    // Export shortlist CSV from bottom bar
    $('#exportShortlist').addEventListener('click', exportShortlistCsv);

    // Clear all
    $('#clearShortlist').addEventListener('click', () => {
      shortlist.clear();
      saveShortlist();
      updateShortlistUI();
      render();
    });

    // View shortlist button → open drawer
    $('#viewShortlist').addEventListener('click', openDrawer);

    // Drawer export / close
    $('#drawerExport').addEventListener('click', exportShortlistCsv);
    $('#drawerClose').addEventListener('click', closeDrawer);
    $('#drawerOverlay').addEventListener('click', closeDrawer);

    // Drawer remove buttons (delegated)
    $('#drawerBody').addEventListener('click', e => {
      const btn = e.target.closest('.drawer-remove-btn');
      if (!btn) return;
      shortlist.delete(btn.dataset.key);
      saveShortlist();
      updateShortlistUI();
      render();
    });

    // Init UI state from loaded shortlist
    updateShortlistUI();
  }

  // ── Shortlist drawer ──
  function openDrawer() {
    renderDrawer();
    $('#shortlistDrawer').classList.remove('hidden');
    $('#drawerOverlay').classList.remove('hidden');
  }

  function closeDrawer() {
    $('#shortlistDrawer').classList.add('hidden');
    $('#drawerOverlay').classList.add('hidden');
  }

  function renderDrawer() {
    const items = [...shortlist].map(k => slStartup(k));
    $('#drawerCount').textContent = items.length;
    if (!items.length) {
      $('#drawerBody').innerHTML = '<tr><td colspan="9" style="text-align:center;padding:32px;color:var(--text-muted)">No startups shortlisted yet - click any row or card to add.</td></tr>';
      return;
    }
    $('#drawerBody').innerHTML = items.map((s, i) => {
      const k = slKey(s);
      const li = s.linkedin_url
        ? `<a href="${s.linkedin_url}" target="_blank" rel="noopener" class="linkedin-link">Profile</a>`
        : '<span class="linkedin-link missing">--</span>';
      return `<tr>
        <td class="row-number">${i + 1}</td>
        <td class="founder-name">${esc(s.founder_name)}</td>
        <td><strong>${esc(s.startup_name)}</strong></td>
        <td><span class="badge ${sectorBadgeClass(s.sector)}">${esc(s.sector)}</span></td>
        <td><span class="tier tier-${s.tier}">${s.tier}</span></td>
        <td>${s.funding_stage ? `<span class="funding-tag funding-${fundingClass(s.funding_stage)}">${esc(s.funding_stage)}</span>` : '-'}</td>
        <td>${s.city ? `<span class="city-tag">${esc(s.city)}</span>` : '-'}</td>
        <td>${li}</td>
        <td><button class="drawer-remove-btn" data-key="${esc(k)}" title="Remove">&#10005;</button></td>
      </tr>`;
    }).join('');
  }

  // ── Shortlist CSV export ──
  function exportShortlistCsv() {
    if (!shortlist.size) { showToast('No startups in shortlist yet.', 'error'); return; }
    const items = [...shortlist].map(k => slStartup(k));
    const headers = ['#', 'Founder', 'Startup', 'Sector', 'One-Liner', 'Tier', 'Tier Rationale', 'Funding Stage', 'City', 'LinkedIn', 'Website', 'Source', 'Founded'];
    const rows = items.map((s, i) => [
      i + 1,
      csvSafe(s.founder_name), csvSafe(s.startup_name), csvSafe(s.sector),
      csvSafe(s.one_liner), s.tier, csvSafe(s.tier_rationale),
      csvSafe(s.funding_stage), csvSafe(s.city),
      s.linkedin_url || '', s.website || '',
      csvSafe(s.source), s.founded_year,
    ]);
    const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    const date = new Date().toISOString().slice(0, 10);
    download(csv, `shortlist_${date}.csv`, 'text/csv');
    showToast(`Exported ${items.length} startups to CSV.`, 'success');
  }

  // ── Scraper ──
  async function runScraper() {
    // Scraping runs in the Python pipeline via GitHub Actions (Worker time limits
    // are too short for it), so the dashboard only points the user there.
    showToast('Scraping runs from GitHub Actions: open the repo, go to Actions, choose "Deal Flow Pipeline", then "Run workflow". See the README.', 'success');
  }

  // ── Toast ──
  let toastTimer;
  function showToast(message, type = 'success') {
    const toast = $('#toast');
    toast.textContent = message;
    toast.className = `toast toast-${type}`;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { toast.className = 'toast hidden'; }, type === 'success' ? 5000 : 7000);
  }

  // ── Export ──
  // If connected to API, use server-side export; otherwise client-side.
  function exportCsv() {
    if (apiConnected && API_BASE) {
      window.open(`${API_BASE}/api/export/csv`, '_blank');
      return;
    }
    const headers = ['#', 'Founder', 'Startup', 'Sector', 'One-Liner', 'Tier', 'Tier Rationale', 'LinkedIn', 'Website', 'Source', 'Founded'];
    const rows = filteredData.map((s, i) => [
      i + 1, csvSafe(s.founder_name), csvSafe(s.startup_name), csvSafe(s.sector),
      csvSafe(s.one_liner), s.tier, csvSafe(s.tier_rationale),
      s.linkedin_url || '', s.website || '', csvSafe(s.source), s.founded_year
    ]);
    const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    download(csv, 'deal_flow_pipeline.csv', 'text/csv');
  }

  function exportJson() {
    if (apiConnected && API_BASE) {
      window.open(`${API_BASE}/api/export/json`, '_blank');
      return;
    }
    download(JSON.stringify(filteredData, null, 2), 'deal_flow_pipeline.json', 'application/json');
  }

  function download(content, filename, type) {
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }

  // ── Utils ──
  function esc(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  function csvSafe(str) {
    if (!str) return '';
    if (str.includes(',') || str.includes('"') || str.includes('\n')) {
      return '"' + str.replace(/"/g, '""') + '"';
    }
    return str;
  }

  function debounce(fn, ms) {
    let t;
    return function (...args) {
      clearTimeout(t);
      t = setTimeout(() => fn.apply(this, args), ms);
    };
  }
})();
