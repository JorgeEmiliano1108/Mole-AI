// chatWidget.js — FE-DT16 UI layer for chat (animations, FAB state)
// API calls delegated to canonical chat.js service module

function updateFabOnOpen() {
    const fab = document.getElementById('chat-fab-btn');
    if (!fab) return;
    fab.style.opacity = '0';
    fab.style.pointerEvents = 'none';
    fab.style.transform = 'scale(0.7)';
}

function updateFabOnClose() {
    const fab = document.getElementById('chat-fab-btn');
    if (!fab) return;
    fab.style.opacity = '1';
    fab.style.pointerEvents = 'auto';
    fab.style.transform = 'scale(1)';
}

export function showSuggestedActions() {
    const suggested = document.getElementById('chat-suggested-actions');
    if (suggested) suggested.style.display = '';
}

function initChat() {
    const box = document.getElementById('chat-messages');
    if (!box || box.children.length > 0) return;
    showSuggestedActions();
}

document.body.addEventListener('click', (e) => {
    const el = e.target.closest('[data-action]');
    if (!el) return;
    const action = el.getAttribute('data-action');
    if (action === 'open-chat') { e.preventDefault(); updateFabOnOpen(); }
    if (action === 'close-chat') { e.preventDefault(); updateFabOnClose(); }
}, true);

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initChat);
} else {
    initChat();
}
