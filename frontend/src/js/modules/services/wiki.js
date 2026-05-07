// ==========================================================
// Wiki service – fetches plant species catalog and renders cards
// ==========================================================

export async function loadWiki() {
    const token = window.getAuthToken ? window.getAuthToken() : null;
    const grid = document.getElementById('wiki-grid');
    if (!grid) {
        console.warn('Wiki grid container not found');
        return;
    }
    // Show loading placeholder
    grid.innerHTML = '<p class="text-mole-dim crt-text-glow-dim animate-pulse">Cargando enciclopedia...</p>';

    if (!token) {
        console.warn('No auth token – wiki cannot load');
        grid.innerHTML = '<p class="text-mole-red">Sesión caducada. Inicia sesión nuevamente.</p>';
        return;
    }
    try {
        const resp = await fetch(`${window.AppConfig.API_BASE_URL}/plants/species/`, {
            method: 'GET',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const species = await resp.json(); // Expect array of objects
        renderWikiCards(species);
    } catch (e) {
        console.error('Failed to load species catalog:', e);
        grid.innerHTML = '<p class="text-mole-red">Error al sincronizar enciclopedia.</p>';
    }
}

function renderWikiCards(list) {
    const grid = document.getElementById('wiki-grid');
    if (!grid) return;
    grid.innerHTML = '';
    list.forEach(item => {
        const card = document.createElement('div');
        card.className = 'wiki-card bg-mole-surface border border-mole-border rounded-lg p-2 hover:shadow-lg transition-shadow';

        const imgWrapper = document.createElement('div');
        imgWrapper.className = 'image-wrapper h-48 flex items-center justify-center mb-2';
        const img = document.createElement('img');
        if (item.image_url) {
            img.src = item.image_url;
            img.alt = `${item.nombre} image`;
            img.className = 'max-h-full max-w-full object-contain';
        } else {
            // Render placeholder for missing image
            imgWrapper.innerHTML = '<svg class="w-12 h-12 text-mole-dim" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 14l2-2 4 4m0-8a4 4 0 11-8 0 4 4 0 018 0z"/></svg><span class="text-xs text-mole-dim block mt-1">[ NO IMAGE DATA ]</span>';
        }
        if (item.image_url) imgWrapper.appendChild(img);
        
        const title = document.createElement('h3');
        title.className = 'text-mole-cyan font-mono text-lg truncate';
        title.textContent = item.nombre || '---';

        const sci = document.createElement('p');
        sci.className = 'text-mole-green font-mono text-sm italic';
        sci.textContent = item.scientific_name || '';

        const desc = document.createElement('p');
        desc.className = 'text-mole-white font-mono text-xs mt-1';
        desc.textContent = item.descripcion || '';

        card.append(imgWrapper, title, sci, desc);
        grid.appendChild(card);
    });
}
