const API = 'http://localhost:8000';

// --- Map ---
const map = L.map('map', { center: [32.5, -119.5], zoom: 6 })
  .addLayer(L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '© OpenStreetMap © CARTO', subdomains: 'abcd', maxZoom: 14,
  }));

// --- State ---
let allStations = [];
let allVariables = [];
let markers = {};
let activeCategory = null;
let selectedVariable = null;
let dropdownFocusIdx = -1;

// --- Station markers ---
function makeMarkerStyle(highlighted) {
  return {
    radius:      highlighted ? 9 : 7,
    fillColor:   highlighted ? '#00c2ff' : '#1a4a6e',
    color:       highlighted ? '#00ffb3' : '#0d7aad',
    weight:      1.5,
    fillOpacity: highlighted ? 0.95 : 0.7,
    opacity:     1,
  };
}

function dimMarkerStyle() {
  return { fillColor: '#0d2a40', color: '#0d4060', fillOpacity: 0.2, radius: 5 };
}

async function loadStations() {
  console.log("LOADING STATIONS");
  try {
    const res = await fetch(`${API}/stations`);
    const data = await res.json();

    const stations = Array.isArray(data) ? data : data?.data;

    if (!Array.isArray(stations)) {
      console.error("Stations format invalid:", data);
      return;
    }

    stations.forEach(station => {
      if (!station.lat || !station.lon) return;

      const marker = L.circleMarker([station.lat, station.lon], {
        radius: 10,
        color: '#00c2ff',
        fillOpacity: 0.7
      }).addTo(map);
      markers[station.station_id] = marker;

      marker.on('click', () => openStation(station));
    });

  } catch (err) {
    console.error("Failed to load stations:", err);
  }
}

// --- Variables + categories ---
async function loadVariables() {
  const res = await fetch(`${API}/variables`);
  allVariables = await res.json();
  document.getElementById('variable-count').textContent = allVariables.length;

  const catRes = await fetch(`${API}/categories`);
  const categories = await catRes.json();
  renderCategoryFilters(categories);
}

function renderCategoryFilters(categories) {
  const container = document.getElementById('category-filters');
  categories.forEach(cat => {
    const btn = document.createElement('button');
    btn.className = 'filter-btn';
    btn.textContent = cat;
    btn.onclick = () => toggleCategory(cat, btn);
    container.appendChild(btn);
  });
}

// --- Dropdown search ---
const searchInput = document.getElementById('search');
const dropdown   = document.getElementById('dropdown');

searchInput.addEventListener('input', () => {
  const q = searchInput.value.trim();
  dropdownFocusIdx = -1;
  if (!q) { closeDropdown(); clearHighlights(); return; }
  renderDropdown(q);
});

searchInput.addEventListener('keydown', e => {
  const items = dropdown.querySelectorAll('.dropdown-item');
  if (e.key === 'ArrowDown') {
    e.preventDefault();
    dropdownFocusIdx = Math.min(dropdownFocusIdx + 1, items.length - 1);
    updateDropdownFocus(items);
  } else if (e.key === 'ArrowUp') {
    e.preventDefault();
    dropdownFocusIdx = Math.max(dropdownFocusIdx - 1, 0);
    updateDropdownFocus(items);
  } else if (e.key === 'Enter') {
    if (dropdownFocusIdx >= 0 && items[dropdownFocusIdx]) {
      items[dropdownFocusIdx].click();
    }
  } else if (e.key === 'Escape') {
    closeDropdown();
  }
});

searchInput.addEventListener('blur', () => {
  // small delay so clicks on dropdown register first
  setTimeout(closeDropdown, 150);
});

function renderDropdown(query) {
  const q = query.toLowerCase();
  let matches = allVariables.filter(v => v.name.toLowerCase().includes(q));

  // also filter by active category if set
  if (activeCategory) matches = matches.filter(v => v.category === activeCategory);

  dropdown.innerHTML = '';
  if (matches.length === 0) {
    dropdown.innerHTML = '<div class="dropdown-empty">No variables found</div>';
    dropdown.classList.add('open');
    return;
  }

  matches.slice(0, 30).forEach((v, i) => {
    const item = document.createElement('div');
    item.className = 'dropdown-item';
    item.dataset.idx = i;

    // Highlight matching part of name
    const nameHtml = v.name.replace(new RegExp(`(${escapeRe(query)})`, 'gi'), '<mark>$1</mark>');

    item.innerHTML = `
      <span class="dropdown-name">${nameHtml}</span>
      <span class="dropdown-meta">
        <span class="dropdown-category">${v.category}</span>
        <span class="dropdown-source">· ${v.source}</span>
        <span class="dropdown-count">(${v.station_count})</span>
      </span>`;

    item.addEventListener('mousedown', () => selectVariable(v));
    dropdown.appendChild(item);
  });

  dropdown.classList.add('open');
}

function updateDropdownFocus(items) {
  items.forEach((el, i) => el.classList.toggle('focused', i === dropdownFocusIdx));
  if (items[dropdownFocusIdx]) items[dropdownFocusIdx].scrollIntoView({ block: 'nearest' });
}

function closeDropdown() {
  dropdown.classList.remove('open');
  dropdownFocusIdx = -1;
}

function selectVariable(variable) {
  selectedVariable = variable;
  searchInput.value = variable.name;
  closeDropdown();

  const ids = new Set(variable.station_ids);
  highlightStations(ids);

  const banner = document.getElementById('search-banner');
  banner.textContent = `${ids.size} stations have "${variable.name}" (${variable.category} · ${variable.source})`;
  banner.classList.add('visible');
  document.getElementById('clear-btn').classList.add('visible');
}

function escapeRe(str) {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// --- Category filter ---
function toggleCategory(cat, btn) {
  if (activeCategory === cat) {
    activeCategory = null;
    btn.classList.remove('active');
    if (!selectedVariable) { clearHighlights(); document.getElementById('clear-btn').classList.remove('visible'); }
  } else {
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    activeCategory = cat;

    // Filter to stations that have any variable in this category
    const ids = new Set();
    allVariables.filter(v => v.category === cat).forEach(v => v.station_ids.forEach(id => ids.add(id)));
    highlightStations(ids);

    const banner = document.getElementById('search-banner');
    banner.textContent = `${ids.size} stations have ${cat} data`;
    banner.classList.add('visible');
    document.getElementById('clear-btn').classList.add('visible');
  }
}

// --- Highlight stations ---
function highlightStations(ids) {
  allStations.forEach(s => {
    const m = markers[s.station_id];
    if (!m) return;
    if (ids.size === 0 || ids.has(s.station_id)) {
      m.setStyle(makeMarkerStyle(true));
    } else {
      m.setStyle(dimMarkerStyle());
    }
  });
}

function clearHighlights() {
  allStations.forEach(s => { if (markers[s.station_id]) markers[s.station_id].setStyle(makeMarkerStyle(true)); });
}

function clearAll() {
  selectedVariable = null;
  activeCategory = null;
  searchInput.value = '';
  closeDropdown();
  clearHighlights();
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('search-banner').classList.remove('visible');
  document.getElementById('clear-btn').classList.remove('visible');
}

function isERDDAP(url) {
  return url && url.includes("erddap/tabledap");
}

function openModal(v) {
  const modalBackdrop = document.getElementById('modal-backdrop');
  const modalTitle = document.getElementById('modal-title');
  const modalBody = document.getElementById('modal-body');
  const footer = document.getElementById('modal-footer');

  modalTitle.textContent = v.name;

  // ---------- BODY ----------
  modalBody.innerHTML = `
    <div class="modal-row">
      <span class="modal-row-label">Source</span>
      <span class="modal-row-value accent">${v.source || 'Unknown'}</span>
    </div>

    <div class="modal-row">
      <span class="modal-row-label">Category</span>
      <span class="modal-row-value">${v.category || 'Uncategorized'}</span>
    </div>

    ${v.unit ? `
      <div class="modal-row">
        <span class="modal-row-label">Unit</span>
        <span class="modal-row-value">${v.unit}</span>
      </div>` : ''}

    ${v.date_range_start ? `
      <div class="modal-row">
        <span class="modal-row-label">Date Range</span>
        <span class="modal-row-value">
          ${v.date_range_start} → ${v.date_range_end || 'Present'}
        </span>
      </div>` : ''}

    <div class="modal-row">
      <span class="modal-row-label">Format</span>
      <span class="modal-row-value">${v.format || 'ERDDAP / CSV'}</span>
    </div>

    ${v.notes ? `
      <div class="modal-row">
        <span class="modal-row-label">Notes</span>
        <span class="modal-row-value" style="font-size:10px;color:var(--muted)">
          ${v.notes}
        </span>
      </div>` : ''}
  `;

  // ---------- WARNINGS ----------
  const transitSources = ['Marine Mammals', 'Seabirds', 'Underway'];
  if (transitSources.includes(v.source)) {
    modalBody.innerHTML += `
      <div style="margin-top:12px;padding:10px 12px;
                  background:rgba(255,107,53,0.08);
                  border:1px solid rgba(255,107,53,0.25);
                  border-radius:4px;font-size:10px;color:var(--warm);line-height:1.6;">
        ⚠️ Transit-based data (not fixed stations)
      </div>`;
  }

  const subsetSources = ['DIC', 'Primary Production', 'Phytoplankton', 'Genomics/eDNA'];
  if (subsetSources.includes(v.source)) {
    modalBody.innerHTML += `
      <div style="margin-top:12px;padding:10px 12px;
                  background:rgba(0,194,255,0.06);
                  border:1px solid rgba(0,194,255,0.2);
                  border-radius:4px;font-size:10px;color:var(--muted);line-height:1.6;">
        ℹ️ Available at subset of stations
      </div>`;
  }

  // ---------- FOOTER LOGIC ----------
  const isERDDAP = v.url && v.url.includes("erddap/tabledap");

  if (isERDDAP) {
    const dataset = v.url.split("tabledap/")[1]?.split(".")[0];
    const variable = v.erddap_variable;

    footer.innerHTML = `
      <div style="width:100%;display:flex;flex-direction:column;gap:8px;">
        
        <a class="btn-docs"
           href="${v.url}"
           target="_blank"
           style="text-align:center">
          View Dataset ↗
        </a>
      </div>
    `;

    // Build station-aware query (if available)
    if (window.currentStation && dataset && variable) {
      const s = window.currentStation;

      const query =
        `https://coastwatch.pfeg.noaa.gov/erddap/tabledap/${dataset}.csv?` +
        `${variable},latitude,longitude,time` +
        `&latitude>=${s.lat - 0.1}&latitude<=${s.lat + 0.1}` +
        `&longitude>=${s.lon - 0.1}&longitude<=${s.lon + 0.1}`;

      document.getElementById('erddap-download').href = query;
    } else {
      document.getElementById('erddap-download').href = v.url;
    }

  } else {
    footer.innerHTML = `
      <a class="btn-docs"
         href="${v.url}"
         target="_blank"
         style="flex:1;text-align:center">
        View Data Source ↗
      </a>
    `;
  }

  modalBackdrop.classList.add('open');
}

function closeModal(e) {
  if (e && e.target !== document.getElementById('modal-backdrop')) return;
  document.getElementById('modal-backdrop').classList.remove('open');
}

document.addEventListener('keydown', e => { if (e.key === 'Escape') document.getElementById('modal-backdrop').classList.remove('open'); });
async function openStation(station) {
  window.currentStation = station;
  document.getElementById('panel-empty').style.display = 'none';
  document.getElementById('panel-header').style.display = 'block';
  document.getElementById('panel-station-id').textContent = `Station ${station.station_id}`;
  document.getElementById('panel-coords').textContent =
    `${station.lat.toFixed(4)}°N  ${Math.abs(station.lon).toFixed(4)}°W`;

  const content = document.getElementById('panel-content');
  content.classList.add('visible');
  content.innerHTML = '<div class="loading">Loading data…</div>';

  const res = await fetch(`${API}/stations/${encodeURIComponent(station.station_id)}`);
  const data = await res.json();

  // Group by source, then category
  const bySource = {};
  data.data.forEach(d => {
    if (!bySource[d.source]) bySource[d.source] = {};
    if (!bySource[d.source][d.category]) bySource[d.source][d.category] = [];
    bySource[d.source][d.category].push(d);
  });

  content.innerHTML = Object.entries(bySource).map(([source, cats]) => `
    <div class="source-group">
      <div class="source-label">📦 ${source}</div>
      ${Object.entries(cats).map(([cat, vars]) => `
        <div class="category-sublabel">${cat}</div>
        ${vars.map((v, i) => `
          <div class="data-link" onclick='openModal(${JSON.stringify(v)})'>
            <span class="data-link-name">${v.name}</span>
            <span class="data-link-unit">${v.unit}</span>
            <span class="data-link-arrow">⬇</span>
          </div>`).join('')}
      `).join('')}
    </div>`).join('');
}

// --- Boot ---
loadStations();
loadVariables();