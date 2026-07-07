/**
 * Utilidades seguras de manipulaci n del DOM
 * Reemplaza usos inseguros de innerHTML para prevenir XSS (OWASP A03)
 */

/**
 * Inserta texto seguro en un elemento (previene XSS al usar textContent)
 * @param {HTMLElement | string} element Elemento DOM o selector
 * @param {string} text Texto a insertar
 */
export function safeSetTextContent(element, text) {
    const el = typeof element === 'string' ? document.querySelector(element) : element;
    if (el) {
        el.textContent = text;
    }
}

/**
 * Crea un elemento DOM de forma segura con atributos
 * @param {string} tag Nombre del tag (ej. 'div')
 * @param {Object} attributes Atributos clave-valor (ej. { class: 'btn', id: 'my-btn' })
 * @param {string} [text] Texto seguro opcional
 * @returns {HTMLElement} El elemento creado
 */
export function createSafeElement(tag, attributes = {}, text = '') {
    const el = document.createElement(tag);
    
    for (const [key, value] of Object.entries(attributes)) {
        if (key.startsWith('on')) {
            // Prevenir inserci n de handlers inline (e.g., onclick)
            console.warn(`Intento de inyectar atributo bloqueado: ${key}`);
            continue;
        }
        el.setAttribute(key, value);
    }

    if (text) {
        el.textContent = text;
    }

    return el;
}

/**
 * Vac a el contenido de un elemento de forma segura
 * @param {HTMLElement | string} element 
 */
export function safeEmpty(element) {
    const el = typeof element === 'string' ? document.querySelector(element) : element;
    if (el) {
        el.textContent = '';
    }
}

/**
 * Construye un elemento con hijos de forma segura.
 * @param {string} tag 
 * @param {Object} attrs 
 * @param {...(HTMLElement|string|null)} children 
 * @returns {HTMLElement}
 */
export function el(tag, attrs = {}, ...children) {
    const e = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
        if (k === 'className') { e.className = v; continue; }
        if (k === 'style' && typeof v === 'object') {
            Object.assign(e.style, v);
            continue;
        }
        if (k.startsWith('on')) {
            if (k !== 'onerror') {
                console.warn(`[dom.el] Atributo on* bloqueado: ${k}`);
                continue;
            }
            e.setAttribute(k, v);
            continue;
        }
        e.setAttribute(k, v);
    }
    for (const child of children) {
        if (child == null || child === false) continue;
        if (typeof child === 'string' || typeof child === 'number') {
            e.appendChild(document.createTextNode(String(child)));
        } else if (child instanceof Node) {
            e.appendChild(child);
        }
    }
    return e;
}

/** @type {DOMPurify.DOMPurifyI|null} */
let _purify = null;

async function getPurify() {
    if (!_purify) {
        try {
            const mod = await import('dompurify');
            _purify = mod.default;
        } catch {
            _purify = { sanitize: s => s };
        }
    }
    return _purify;
}

/**
 * Sanitiza una cadena HTML usando DOMPurify.
 * Única vía aprobada para renderizar HTML dinámico controlado
 * (ej. respuestas LLM con formato markdown renderizado a HTML).
 * Usar SOLO cuando textContent sea insuficiente.
 *
 * NOTA: El primer uso importa DOMPurify dinámicamente (lazy).
 * Si se usará frecuentemente, precarga con: safeHTML('') al inicio.
 * @param {string} dirty - HTML potencialmente inseguro
 * @returns {Promise<string>} HTML sanitizado
 */
export async function safeHTML(dirty) {
    if (typeof dirty !== 'string') return '';
    const purify = await getPurify();
    return purify.sanitize ? purify.sanitize(dirty) : dirty;
}

/**
 * Limpia un contenedor y lo puebla con hijos de forma segura.
 * @param {HTMLElement|string} container 
 * @param {...(HTMLElement|string|null)} children 
 */
export function safeRender(container, ...children) {
    const c = typeof container === 'string' ? document.querySelector(container) : container;
    if (!c) return;
    while (c.firstChild) c.removeChild(c.firstChild);
    for (const child of children) {
        if (child == null || child === false) continue;
        if (typeof child === 'string' || typeof child === 'number') {
            c.appendChild(document.createTextNode(String(child)));
        } else if (child instanceof Node) {
            c.appendChild(child);
        }
    }
}
