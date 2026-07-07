import { describe, it, expect, vi, beforeEach } from 'vitest';
import { el, safeRender, safeHTML, safeEmpty, safeSetTextContent, createSafeElement } from '../ui/dom.js';

describe('el()', () => {
  it('creates a div with class and text', () => {
    const e = el('div', { class: 'foo' }, 'hello');
    expect(e.tagName).toBe('DIV');
    expect(e.getAttribute('class')).toBe('foo');
    expect(e.textContent).toBe('hello');
  });

  it('creates element with className shorthand', () => {
    const e = el('span', { className: 'bar' });
    expect(e.className).toBe('bar');
  });

  it('sets object style', () => {
    const e = el('div', { style: { color: 'red', fontSize: '14px' } });
    expect(e.style.color).toBe('red');
    expect(e.style.fontSize).toBe('14px');
  });

  it('blocks onclick attribute', () => {
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => {});
    const e = el('button', { onclick: 'alert(1)' });
    expect(e.getAttribute('onclick')).toBeNull();
    expect(warn).toHaveBeenCalledWith('[dom.el] Atributo on* bloqueado: onclick');
    warn.mockRestore();
  });

  it('allows onerror attribute for image fallback', () => {
    const e = el('img', { onerror: "this.src='/fallback.png'" });
    expect(e.getAttribute('onerror')).toBe("this.src='/fallback.png'");
  });

  it('skips null/false children', () => {
    const e = el('ul', {}, el('li', {}, 'a'), null, false, el('li', {}, 'b'));
    expect(e.children.length).toBe(2);
    expect(e.children[1].textContent).toBe('b');
  });

  it('accepts number as child', () => {
    const e = el('div', {}, 42);
    expect(e.textContent).toBe('42');
  });

  it('sets arbitrary attributes', () => {
    const e = el('a', { href: '/test', 'data-id': '123' });
    expect(e.getAttribute('href')).toBe('/test');
    expect(e.getAttribute('data-id')).toBe('123');
  });
});

describe('safeRender()', () => {
  it('renders children into container', () => {
    document.body.innerHTML = '<div id="target"></div>';
    const container = document.getElementById('target');
    safeRender(container, el('p', {}, 'text'), 'text node');
    expect(container.children.length).toBe(1);
    expect(container.textContent).toBe('texttext node');
  });

  it('clears previous content', () => {
    document.body.innerHTML = '<div id="target"><span>old</span></div>';
    const container = document.getElementById('target');
    safeRender(container, el('p', {}, 'new'));
    expect(container.children.length).toBe(1);
    expect(container.textContent).toBe('new');
  });

  it('accepts string selector', () => {
    document.body.innerHTML = '<div id="sel"></div>';
    safeRender('#sel', 'hello');
    expect(document.getElementById('sel').textContent).toBe('hello');
  });

  it('ignores null/false children', () => {
    document.body.innerHTML = '<div id="c"></div>';
    safeRender('#c', null, false);
    expect(document.getElementById('c').textContent).toBe('');
  });

  it('does nothing if container not found', () => {
    expect(() => safeRender('#nonexistent', 'x')).not.toThrow();
  });
});

describe('safeHTML()', () => {
  it('returns empty string for non-string input', async () => {
    expect(await safeHTML(null)).toBe('');
    expect(await safeHTML(undefined)).toBe('');
    expect(await safeHTML(42)).toBe('');
  });

  it('strips script tags', async () => {
    const result = await safeHTML('<script>alert(1)</script><p>safe</p>');
    expect(result).not.toContain('<script>');
    expect(result).toContain('<p>safe</p>');
  });

  it('strips on* event handlers', async () => {
    const result = await safeHTML('<img src=x onerror=alert(1)>');
    expect(result).not.toContain('onerror');
  });

  it('allows safe tags', async () => {
    const result = await safeHTML('<b>bold</b> <i>italic</i>');
    expect(result).toContain('<b>bold</b>');
    expect(result).toContain('<i>italic</i>');
  });
});

describe('safeEmpty()', () => {
  it('clears element content', () => {
    document.body.innerHTML = '<div id="e"><span>content</span></div>';
    safeEmpty('#e');
    expect(document.getElementById('e').textContent).toBe('');
  });

  it('accepts element reference', () => {
    const div = document.createElement('div');
    div.textContent = 'text';
    safeEmpty(div);
    expect(div.textContent).toBe('');
  });

  it('noop for non-existent selector', () => {
    expect(() => safeEmpty('#nonexistent')).not.toThrow();
  });
});

describe('safeSetTextContent()', () => {
  it('sets text content safely', () => {
    document.body.innerHTML = '<p id="p"></p>';
    safeSetTextContent('#p', '<b>not html</b>');
    expect(document.getElementById('p').textContent).toBe('<b>not html</b>');
    expect(document.getElementById('p').innerHTML).toBe('&lt;b&gt;not html&lt;/b&gt;');
  });
});

describe('createSafeElement()', () => {
  it('blocks on* attributes', () => {
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => {});
    const e = createSafeElement('button', { onclick: 'evil()' });
    expect(e.getAttribute('onclick')).toBeNull();
    expect(warn).toHaveBeenCalled();
    warn.mockRestore();
  });

  it('sets normal attributes', () => {
    const e = createSafeElement('a', { href: '/valid', class: 'link' });
    expect(e.getAttribute('href')).toBe('/valid');
    expect(e.getAttribute('class')).toBe('link');
  });

  it('sets text content', () => {
    const e = createSafeElement('p', {}, 'hello');
    expect(e.textContent).toBe('hello');
  });
});
