// View switching logic extracted from dashboard.html
export function switchFieldView(viewId) {
    document.querySelectorAll('.field-view').forEach(v => v.classList.add('hidden'));
    const target = document.getElementById(viewId);
    if (target) target.classList.remove('hidden');
    // Trigger wiki load when wiki view activated
    if (viewId === 'view-wiki' && typeof window.loadWiki === 'function') {
        window.loadWiki();
    }
    // Trigger map init when mapa view activated
    if (viewId === 'view-mapa' && typeof window.initMapView === 'function') {
        setTimeout(() => window.initMapView(), 100);
    }
    // Trigger IoT init when iot view activated
    if (viewId === 'view-iot' && typeof window.initIoTView === 'function') {
        window.initIoTView();
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

// Expose globally for inline onclick handlers
window.switchFieldView = switchFieldView;
