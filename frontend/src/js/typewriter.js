/**
 * Typewriter effect – minimal, auto-init on DOMContentLoaded.
 * Usage: add `data-typewriter="Your text"` (optional `data-speed` in ms per char) to any element.
 */
import { attachCursor, detachCursor } from './modules/ui/cursor.js';

export function typewriter(el, options = {}) {
  const text = el.getAttribute('data-typewriter') || '';
  const speed = Number(el.getAttribute('data-speed')) || options.speed || 50;
  detachCursor(el);
  el.textContent = '';
  let i = 0;
  const step = () => {
    if (i < text.length) {
      el.textContent += text.charAt(i);
      i++;
      setTimeout(step, speed);
    }
  };
  step();
  setTimeout(() => attachCursor(el), text.length * speed + 50);
}

if (typeof document !== 'undefined') {
  document.addEventListener('DOMContentLoaded', () => {
    const els = document.querySelectorAll('[data-typewriter]');
    els.forEach(el => {
      typewriter(el);
    });
  });
}