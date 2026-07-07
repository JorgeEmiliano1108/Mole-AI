// View switching logic extracted from dashboard.html
// Lazy loaders registered by main.js to avoid layer violations (ui -> services)

import { loadWiki } from '../services/wiki.js';
import { initIoTView } from '../services/iot.js';

const _lazyLoaders = {};

export function registerLazyLoader(viewId, loaderFn) {
    _lazyLoaders[viewId] = loaderFn;
}

export function switchFieldView(viewId) {
    document.querySelectorAll('.field-view').forEach(v => v.classList.add('hidden'));
    const target = document.getElementById(viewId);
    if (target) target.classList.remove('hidden');
    // Trigger wiki load when wiki view activated
    if (viewId === 'view-wiki') {
        loadWiki();
    }
    // Trigger lazy-loaded modules via registry (set by main.js)
    if (_lazyLoaders[viewId]) {
        setTimeout(async () => {
            const mod = await _lazyLoaders[viewId]();
            if (mod && typeof mod.initMapView === 'function') mod.initMapView();
        }, 100);
    }
    // Trigger IoT init when iot view activated
    if (viewId === 'view-iot') {
        initIoTView();
    }
    // Update nav button styles
    document.querySelectorAll('nav button').forEach(btn => {
        const onclick = btn.getAttribute('onclick') || '';
        if (onclick.includes(viewId)) {
            btn.classList.remove('text-mole-dim');
            btn.classList.add('text-mole-cyan');
        } else {
            btn.classList.remove('text-mole-cyan');
            btn.classList.add('text-mole-dim');
        }
    });
}