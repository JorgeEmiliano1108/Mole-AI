/**
 * Terminal-style blinking cursor helper.
 * Attach a block cursor ("█") that blinks after the supplied element.
 * The cursor element receives the class `cursor-blink` so it can be removed
 * later and styled via Tailwind (`animate-cursor-blink`).
 */
export function attachCursor(el) {
  if (el.querySelector('.cursor-blink')) return;
  const cursor = document.createElement('span');
  cursor.className = 'cursor-blink animate-cursor-blink text-mole-cyan';
  cursor.textContent = '█';
  el.appendChild(cursor);
}

export function detachCursor(el) {
  const cur = el.querySelector('.cursor-blink');
  if (cur) cur.remove();
}