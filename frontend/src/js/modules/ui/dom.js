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
