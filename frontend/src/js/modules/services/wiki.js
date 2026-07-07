import { el, safeRender } from '../ui/dom.js';
import { apiService } from '../api/ApiService.js';

const WIKI_CATEGORY_BADGE = { planta: 'PLANTA', plaga: 'PLAGA', enfermedad: 'ENFERMEDAD' };
const WIKI_CATEGORY_COLOR = { planta: 'border-mole-green', plaga: 'border-mole-amber', enfermedad: 'border-mole-red' };

function renderWikiCard(item) {
    const name = item.common_name || item.nombre || item.scientific_name || '';
    const sciName = item.scientific_name || item.nombre_cientifico || '';
    const desc = item.description || item.descripcion || '';
    const cat = item.category || 'planta';
    const imgSrc = (item.image_url && item.image_url !== 'undefined') ? item.image_url : '/assets/topo.png';
    const catBadge = WIKI_CATEGORY_BADGE[cat] || 'ESPECIE';
    const catBorder = WIKI_CATEGORY_COLOR[cat] || 'border-mole-cyan';
    const itemId = String(item.id || '').slice(0, 8).toUpperCase();

    const badges = [];
    if (item.is_protected_nom059) {
        badges.push(
            el('span', { className: 'px-2 py-0.5 bg-mole-red/20 text-mole-red text-[9px] border border-mole-red/40 font-bold' }, 'NOM-059')
        );
    }

    const humBadgeText = item.ideal_humidity_min != null
        ? `H: ${item.ideal_humidity_min}-${item.ideal_humidity_max}%`
        : (item.humedad ? `H: ${item.humedad}` : null);
    const tempBadgeText = item.ideal_temp_min != null
        ? `T: ${item.ideal_temp_min}-${item.ideal_temp_max} C`
        : (item.temperatura ? `T: ${item.temperatura}` : null);
    const phBadgeText = item.ideal_ph_min != null
        ? `pH: ${item.ideal_ph_min}-${item.ideal_ph_max}`
        : (item.ph ? `pH: ${item.ph}` : null);

    const humBadgeEl = humBadgeText ? el('span', { className: 'px-2 py-0.5 bg-sky-900/50 text-sky-400 text-[9px] border border-sky-700/50 font-mono' }, humBadgeText) : null;
    const tempBadgeEl = tempBadgeText ? el('span', { className: 'px-2 py-0.5 bg-orange-900/50 text-orange-400 text-[9px] border border-orange-700/50 font-mono' }, tempBadgeText) : null;
    const phBadgeEl = phBadgeText ? el('span', { className: 'px-2 py-0.5 bg-mole-surface/80 text-mole-cyan text-[9px] border border-mole-border font-mono' }, phBadgeText) : null;

    const overlayBadges = [humBadgeEl, tempBadgeEl, phBadgeEl].filter(Boolean);
    if (item.is_protected_nom059) {
        overlayBadges.push(
            el('span', { className: 'px-2 py-0.5 bg-mole-red/20 text-mole-red text-[9px] border border-mole-red/40' }, 'NOM-059')
        );
    }

    const img = el('img', {
        src: imgSrc,
        alt: name,
        className: 'w-full h-full object-cover grayscale group-hover:grayscale-0 transition-all duration-500 scale-100 group-hover:scale-105',
        onerror: "this.onerror=null; this.src='/assets/topo.png';"
    });

    return el('div', {
        className: `group relative overflow-hidden bg-mole-surface border ${catBorder}/40 hover:${catBorder} rounded-lg cursor-pointer transition-all duration-300 hover:shadow-cyber`
    },
        el('div', { className: 'h-44 overflow-hidden bg-mole-bg flex items-center justify-center' }, img),
        el('div', { className: 'p-3' },
            el('p', { className: 'text-[10px] text-mole-dim font-mono mb-1' },
                catBadge,
                ...badges
            ),
            el('h3', { className: 'text-mole-cyan font-bold text-sm truncate' }, name),
            el('p', { className: 'text-mole-green font-mono text-xs italic truncate' }, sciName)
        ),
        el('div', {
            className: `absolute inset-0 bg-black/90 backdrop-blur-sm p-4 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex flex-col justify-between border-2 ${catBorder}`
        },
            el('div', {},
                el('p', { className: 'text-[10px] text-mole-cyan font-mono mb-1 opacity-60' }, `DATA_SHEET // ${itemId}`),
                el('h4', { className: 'text-white text-sm font-bold mb-1' }, name),
                el('p', { className: 'text-mole-text-dim text-[10px] italic mb-3' }, sciName),
                el('p', { className: 'text-mole-text-dim text-[10px] leading-relaxed line-clamp-4' }, desc || 'Sin descripcion disponible.')
            ),
            el('div', { className: 'flex flex-wrap gap-1.5 mt-3' }, ...overlayBadges)
        )
    );
}

let _wikiDebounceTimer = null;

// Entry point called from main.js on view-wiki activation
export function loadWiki() {
    setupWikiControls();
    fetchAndRender();
}

function setupWikiControls() {
    const searchInput = document.getElementById('wiki-search');
    const catFilter   = document.getElementById('wiki-filter-cat');

    if (searchInput && !searchInput.dataset.wikiInit) {
        searchInput.dataset.wikiInit = '1';
        searchInput.addEventListener('input', () => {
            clearTimeout(_wikiDebounceTimer);
            _wikiDebounceTimer = setTimeout(() => {
                fetchAndRender();
                saveSearchHistory(searchInput.value);
                hideHistoryDropdown();
            }, 500);
        });

        searchInput.addEventListener('focus', () => {
            if (!searchInput.value.trim()) showHistoryDropdown();
        });

        // Hide with delay to allow click on dropdown items
        searchInput.addEventListener('blur', () => {
            setTimeout(hideHistoryDropdown, 200);
        });
    }

    if (catFilter && !catFilter.dataset.wikiInit) {
        catFilter.dataset.wikiInit = '1';
        catFilter.addEventListener('change', fetchAndRender);
    }
}

async function fetchAndRender() {
    const grid    = document.getElementById('wiki-grid');
    const loading = document.getElementById('wiki-loading');
    const countEl = document.getElementById('wiki-count');
    const countNum= document.getElementById('wiki-count-num');

    if (!grid) return;

    const query    = (document.getElementById('wiki-search')?.value || '').trim().toLowerCase();
    const category = document.getElementById('wiki-filter-cat')?.value || '';

    // PATCH-01: Await species cache before filtering locally
    if (window.MoleState && typeof window.MoleState.ensureSpeciesLoaded === 'function') {
        if (!window.MoleState.speciesCatalogLoaded) {
            safeRender(grid,
                el('p', { className: 'text-mole-cyan animate-pulse font-mono text-xs col-span-full' }, 'CARGANDO CATALOGO...')
            );
        }
        await window.MoleState.ensureSpeciesLoaded();
    }

    // If MoleState has cached species, filter locally (zero network)
    if (window.MoleState && window.MoleState.speciesCatalogLoaded && window.MoleState.speciesCatalog.length > 0) {
        let list = window.MoleState.speciesCatalog;

        if (query) {
            list = list.filter(s =>
                (s.scientific_name || '').toLowerCase().includes(query) ||
                (s.common_name || '').toLowerCase().includes(query)
            );
        }
        if (category) {
            list = list.filter(s => s.category === category);
        }

        list = list.slice(0, 50);
        renderWikiCards(list);

        if (countEl && countNum) {
            countNum.textContent = list.length;
            countEl.classList.remove('hidden');
        }
        return;
    }

    // Fallback: fetch from API (first load or if MoleState not ready)
    if (!query && !category) {
        safeRender(grid,
            el('p', { className: 'text-mole-dim font-mono text-sm col-span-full text-center mt-10 opacity-50' },
                '> INGRESA UN TERMINO O SELECCIONA UNA CATEGORIA'
            )
        );
        if (countEl) countEl.classList.add('hidden');
        return;
    }

    if (loading) loading.classList.remove('hidden');
    safeRender(grid,
        el('p', { className: 'text-mole-cyan animate-pulse font-mono text-xs col-span-full' }, 'ESCANEANDO BASE DE DATOS...')
    );

    try {
        const params = new URLSearchParams();
        if (query)    params.set('q', query);
        if (category) params.set('category', category);

        const data = await apiService.get(`plants/search/?${params.toString()}`);
        const list = Array.isArray(data) ? data : [];
        renderWikiCards(list);

        if (countEl && countNum) {
            countNum.textContent = list.length;
            countEl.classList.remove('hidden');
        }
    } catch (e) {
        console.error('[Wiki] Error al buscar:', e);
        safeRender(grid,
            el('p', { className: 'text-mole-red font-mono text-xs col-span-full' }, 'ERROR DE SINCRONIZACION. Intente nuevamente.')
        );
    } finally {
        if (loading) loading.classList.add('hidden');
    }
}

// -- FE-11: Wiki Search History --------------------------------
const HISTORY_KEY = 'moleia_wiki_search_history';

function saveSearchHistory(query) {
    query = query.trim().toLowerCase();
    if (query.length < 2) return;
    
    let history = [];
    try { history = JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]'); } catch (e) {}
    
    // Remove duplicate
    history = history.filter(item => item !== query);
    // Add to top
    history.unshift(query);
    // Limit to 10
    history = history.slice(0, 10);
    
    localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
}

function showHistoryDropdown() {
    const dropdown = document.getElementById('wiki-history-dropdown');
    if (!dropdown) return;
    
    let history = [];
    try { history = JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]'); } catch (e) {}
    
    if (history.length === 0) {
        dropdown.classList.add('hidden');
        return;
    }
    
    const fragment = document.createDocumentFragment();
    history.forEach(function(hItem) {
        const div = document.createElement('div');
        div.className = 'wiki-history-item px-4 py-2 hover:bg-mole-cyan hover:text-mole-base text-mole-cyan text-xs font-mono cursor-pointer transition-colors border-b border-mole-border last:border-0';
        div.setAttribute('data-query', hItem);
        div.textContent = hItem;
        fragment.appendChild(div);
    });
    safeRender(dropdown);
    dropdown.appendChild(fragment);
    
    dropdown.querySelectorAll('.wiki-history-item').forEach(el => {
        el.addEventListener('click', (e) => {
            const searchInput = document.getElementById('wiki-search');
            if (searchInput) {
                searchInput.value = e.currentTarget.dataset.query;
                fetchAndRender();
            }
        });
    });
    
    dropdown.classList.remove('hidden');
}

function hideHistoryDropdown() {
    const dropdown = document.getElementById('wiki-history-dropdown');
    if (dropdown) dropdown.classList.add('hidden');
}


function renderWikiCards(list) {
    const grid = document.getElementById('wiki-grid');
    if (!grid) return;

    if (!list.length) {
        safeRender(grid,
            el('p', { className: 'text-mole-dim font-mono text-sm col-span-full text-center mt-10 opacity-60' },
                '[ SIN RESULTADOS ]'
            )
        );
        return;
    }

    safeRender(grid, ...list.map(function(item) { return renderWikiCard(item); }));
}
