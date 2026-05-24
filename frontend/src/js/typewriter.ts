/**
 * Typewriter effect – minimal, auto‑init on DOMContentLoaded.
 * Usage: add `data-typewriter="Your text"` (optional `data-speed` in ms per char) to any element.
 */
import { attachCursor, detachCursor } from './modules/ui/cursor';

export function typewriter(el: HTMLElement, options: { speed?: number } = {}): void {
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
  // Attach blinking cursor after the animation completes (estimated time)
  setTimeout(() => attachCursor(el), text.length * speed + 50);
}

// Auto‑initialize on page load for any matching elements
if (typeof document !== 'undefined') {
  document.addEventListener('DOMContentLoaded', () => {
    const els = document.querySelectorAll('[data-typewriter]');
    els.forEach(el => {
      // eslint‑disable-next-line @typescript-eslint/ban-ts-comment
      // @ts-ignore – we know el is HTMLElement
      typewriter(el as HTMLElement);
    });
  });
}
