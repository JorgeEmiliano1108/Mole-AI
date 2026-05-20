// ==========================================================
// Wiki Tactica -- SpeciesCatalog browser with MoleState cache
// ==========================================================

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
            _wikiDebounceTimer = setTimeout(fetchAndRender, 300);
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
            grid.innerHTML = '<p class="text-mole-cyan animate-pulse font-mono text-xs col-span-full">CARGANDO CATALOGO...</p>';
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
        grid.innerHTML = '<p class="text-mole-dim font-mono text-sm col-span-full text-center mt-10 opacity-50">> INGRESA UN TERMINO O SELECCIONA UNA CATEGORIA</p>';
        if (countEl) countEl.classList.add('hidden');
        return;
    }

    if (loading) loading.classList.remove('hidden');
    grid.innerHTML = '<p class="text-mole-cyan animate-pulse font-mono text-xs col-span-full">ESCANEANDO BASE DE DATOS...</p>';

    try {
        const params = new URLSearchParams();
        if (query)    params.set('q', query);
        if (category) params.set('category', category);

        const data = await window.ApiService.get(`plants/search/?${params.toString()}`);
        const list = Array.isArray(data) ? data : [];
        renderWikiCards(list);

        if (countEl && countNum) {
            countNum.textContent = list.length;
            countEl.classList.remove('hidden');
        }
    } catch (e) {
        console.error('[Wiki] Error al buscar:', e);
        grid.innerHTML = '<p class="text-mole-red font-mono text-xs col-span-full">ERROR DE SINCRONIZACION. Intente nuevamente.</p>';
    } finally {
        if (loading) loading.classList.add('hidden');
    }
}

function renderWikiCards(list) {
    const grid = document.getElementById('wiki-grid');
    if (!grid) return;

    if (!list.length) {
        grid.innerHTML = '<p class="text-mole-dim font-mono text-sm col-span-full text-center mt-10 opacity-60">[ SIN RESULTADOS ]</p>';
        return;
    }

    const categoryBadge = { planta: 'PLANTA', plaga: 'PLAGA', enfermedad: 'ENFERMEDAD' };
    const categoryColor = { planta: 'border-mole-green', plaga: 'border-mole-amber', enfermedad: 'border-mole-red' };

    grid.innerHTML = list.map(item => {
        // Normalize keys (MoleState uses model fields, API search uses transformed keys)
        const name       = item.common_name || item.nombre || item.scientific_name || '';
        const sciName    = item.scientific_name || item.nombre_cientifico || '';
        const desc       = item.description || item.descripcion || '';
        const cat        = item.category || 'planta';
        const imgSrc     = (item.image_url && item.image_url !== 'undefined') ? item.image_url : '/static/assets/topo.png';
        const catBadge   = categoryBadge[cat] || 'ESPECIE';
        const catBorder  = categoryColor[cat] || 'border-mole-cyan';
        const itemId     = String(item.id || '').slice(0, 8).toUpperCase();

        // NOM-059 badge
        const nomBadge = item.is_protected_nom059
            ? `<span class="px-2 py-0.5 bg-mole-red/20 text-mole-red text-[9px] border border-mole-red/40 font-bold">NOM-059</span>`
            : '';

        // Ideal range badges (from MoleState model fields)
        const humBadge = (item.ideal_humidity_min != null)
            ? `<span class="px-2 py-0.5 bg-sky-900/50 text-sky-400 text-[9px] border border-sky-700/50 font-mono">H: ${item.ideal_humidity_min}-${item.ideal_humidity_max}%</span>`
            : (item.humedad ? `<span class="px-2 py-0.5 bg-sky-900/50 text-sky-400 text-[9px] border border-sky-700/50 font-mono">H: ${item.humedad}</span>` : '');

        const tempBadge = (item.ideal_temp_min != null)
            ? `<span class="px-2 py-0.5 bg-orange-900/50 text-orange-400 text-[9px] border border-orange-700/50 font-mono">T: ${item.ideal_temp_min}-${item.ideal_temp_max} C</span>`
            : (item.temperatura ? `<span class="px-2 py-0.5 bg-orange-900/50 text-orange-400 text-[9px] border border-orange-700/50 font-mono">T: ${item.temperatura}</span>` : '');

        const phBadge = (item.ideal_ph_min != null)
            ? `<span class="px-2 py-0.5 bg-mole-surface/80 text-mole-cyan text-[9px] border border-mole-border font-mono">pH: ${item.ideal_ph_min}-${item.ideal_ph_max}</span>`
            : (item.ph ? `<span class="px-2 py-0.5 bg-mole-surface/80 text-mole-cyan text-[9px] border border-mole-border font-mono">pH: ${item.ph}</span>` : '');

        return `
        <div class="group relative overflow-hidden bg-mole-surface border ${catBorder}/40 hover:${catBorder} rounded-lg cursor-pointer transition-all duration-300 hover:shadow-cyber">
            <div class="h-44 overflow-hidden bg-mole-bg flex items-center justify-center">
                <img
                    src="${imgSrc}"
                    alt="${name}"
                    class="w-full h-full object-cover grayscale group-hover:grayscale-0 transition-all duration-500 scale-100 group-hover:scale-105"
                    onerror="this.onerror=null; this.src='/static/assets/topo.png';"
                >
            </div>
            <div class="p-3">
                <p class="text-[10px] text-mole-dim font-mono mb-1">${catBadge} ${nomBadge}</p>
                <h3 class="text-mole-cyan font-bold text-sm truncate">${name}</h3>
                <p class="text-mole-green font-mono text-xs italic truncate">${sciName}</p>
            </div>
            <div class="absolute inset-0 bg-black/90 backdrop-blur-sm p-4 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex flex-col justify-between border-2 ${catBorder}">
                <div>
                    <p class="text-[10px] text-mole-cyan font-mono mb-1 opacity-60">DATA_SHEET // ${itemId}</p>
                    <h4 class="text-white text-sm font-bold mb-1">${name}</h4>
                    <p class="text-mole-text-dim text-[10px] italic mb-3">${sciName}</p>
                    <p class="text-mole-text-dim text-[10px] leading-relaxed line-clamp-4">${desc || 'Sin descripcion disponible.'}</p>
                </div>
                <div class="flex flex-wrap gap-1.5 mt-3">
                    ${humBadge}${tempBadge}${phBadge}
                    ${item.is_protected_nom059 ? `<span class="px-2 py-0.5 bg-mole-red/20 text-mole-red text-[9px] border border-mole-red/40">NOM-059</span>` : ''}
                </div>
            </div>
        </div>`;
    }).join('');
}
