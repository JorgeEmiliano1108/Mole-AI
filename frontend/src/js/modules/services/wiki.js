// ==========================================================
// Wiki Táctica – búsqueda con debounce, filtros y hover cards
// ==========================================================

let _wikiDebounceTimer = null;

// Punto de entrada llamado desde main.js al mostrar la vista wiki
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

    const query    = (document.getElementById('wiki-search')?.value || '').trim();
    const category = document.getElementById('wiki-filter-cat')?.value || '';

    // Requiere al menos 1 carácter o categoría seleccionada para buscar
    if (!query && !category) {
        grid.innerHTML = '<p class="text-mole-dim font-mono text-sm col-span-full text-center mt-10 opacity-50">> INGRESA UN TÉRMINO O SELECCIONA UNA CATEGORÍA</p>';
        if (countEl) countEl.classList.add('hidden');
        return;
    }

    // Loading state
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
        grid.innerHTML = '<p class="text-mole-red font-mono text-xs col-span-full">ERROR DE SINCRONIZACIÓN. Intente nuevamente.</p>';
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

    const categoryBadge = { planta: '🌿 PLANTA', plaga: '🐛 PLAGA', enfermedad: '🦠 ENFERMEDAD' };
    const categoryColor  = { planta: 'border-mole-green', plaga: 'border-mole-amber', enfermedad: 'border-mole-red' };

    grid.innerHTML = list.map(item => {
        const imgSrc     = (item.image_url && item.image_url !== 'undefined') ? item.image_url : '/static/assets/topo.png';
        const catBadge   = categoryBadge[item.category] || '📋 ESPECIE';
        const catBorder  = categoryColor[item.category] || 'border-mole-cyan';
        const nomBadge   = item.is_protected_nom059
            ? `<span class="px-2 py-0.5 bg-mole-red/20 text-mole-red text-[9px] border border-mole-red/40 font-bold">NOM-059 ⚠</span>`
            : '';

        return `
        <div class="group relative overflow-hidden bg-mole-surface border ${catBorder}/40 hover:${catBorder} rounded-lg cursor-pointer transition-all duration-300 hover:shadow-cyber">
            <!-- Imagen -->
            <div class="h-44 overflow-hidden bg-mole-bg flex items-center justify-center">
                <img
                    src="${imgSrc}"
                    alt="${item.nombre}"
                    class="w-full h-full object-cover grayscale group-hover:grayscale-0 transition-all duration-500 scale-100 group-hover:scale-105"
                    onerror="this.onerror=null; this.src='/static/assets/topo.png';"
                >
            </div>
            <!-- Info Base -->
            <div class="p-3">
                <p class="text-[10px] text-mole-dim font-mono mb-1">${catBadge} ${nomBadge}</p>
                <h3 class="text-mole-cyan font-bold text-sm truncate">${item.nombre}</h3>
                <p class="text-mole-green font-mono text-xs italic truncate">${item.nombre_cientifico || ''}</p>
            </div>
            <!-- OVERLAY: Ficha Técnica (CSS :hover via group-hover) -->
            <div class="absolute inset-0 bg-black/90 backdrop-blur-sm p-4 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex flex-col justify-between border-2 ${catBorder}">
                <div>
                    <p class="text-[10px] text-mole-cyan font-mono mb-1 opacity-60">DATA_SHEET // ${String(item.id).slice(0,8).toUpperCase()}</p>
                    <h4 class="text-white text-sm font-bold mb-1">${item.nombre}</h4>
                    <p class="text-mole-text-dim text-[10px] italic mb-3">${item.nombre_cientifico || ''}</p>
                    <p class="text-mole-text-dim text-[10px] leading-relaxed line-clamp-4">${item.descripcion || 'Sin descripción disponible.'}</p>
                </div>
                <div class="flex flex-wrap gap-1.5 mt-3">
                    ${item.humedad    ? `<span class="px-2 py-0.5 bg-sky-900/50 text-sky-400 text-[9px] border border-sky-700/50 font-mono">H: ${item.humedad}</span>` : ''}
                    ${item.temperatura ? `<span class="px-2 py-0.5 bg-orange-900/50 text-orange-400 text-[9px] border border-orange-700/50 font-mono">T: ${item.temperatura}</span>` : ''}
                    ${item.ph        ? `<span class="px-2 py-0.5 bg-mole-surface/80 text-mole-cyan text-[9px] border border-mole-border font-mono">pH: ${item.ph}</span>` : ''}
                    ${item.is_protected_nom059 ? `<span class="px-2 py-0.5 bg-mole-red/20 text-mole-red text-[9px] border border-mole-red/40">NOM-059 ⚠</span>` : ''}
                </div>
            </div>
        </div>`;
    }).join('');
}
