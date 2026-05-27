// sanitize.js – removes non‑ASCII characters from JS source
// Used by the SRE team to fix Vite/Rollup build failures.
// This script walks the directory frontend/src/js/**/*.js and:
//   * In comments (// … or /* … */) replaces any character > 0x7F with a sensible ASCII fallback.
//   * In string literals (single, double, template) replaces any character > 0x7F with a \uXXXX escape.
// It writes the file back only when a change was made.

const fs = require('fs');
const path = require('path');

// Mapping for common Unicode punctuation that appears in comments.
const commentMap = {
  '–': '-', // EN DASH
  '—': '-', // EM DASH
  '→': '->',
  '←': '<-',
  '↑': '^',
  '↓': 'v',
  '•': '-',
  '\u00A0': ' ', // NO‑BREAK SPACE
  '\u202F': ' ', // NARROW NO‑BREAK SPACE
  '\u2009': ' ', // THIN SPACE
  '\u2003': ' ', // EM SPACE
};

function replaceInComment(text) {
  // Replace each mapped char; anything else >0x7F we replace with a space.
  let result = '';
  for (const ch of text) {
    const code = ch.charCodeAt(0);
    if (code <= 0x7f) {
      result += ch;
    } else if (commentMap[ch]) {
      result += commentMap[ch];
    } else {
      // generic fallback – space to keep layout readable
      result += ' ';
    }
  }
  return result;
}

function replaceInString(text) {
  // Convert each non‑ASCII character to a \uXXXX escape.
  let result = '';
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    const code = ch.codePointAt(0);
    if (code <= 0x7f) {
      result += ch;
    } else {
      // For code points above 0xFFFF we need surrogate pairs.
      if (code <= 0xffff) {
        result += '\\u' + code.toString(16).padStart(4, '0');
      } else {
        // Encode as two UTF‑16 code units.
        const high = Math.floor((code - 0x10000) / 0x400) + 0xd800;
        const low = ((code - 0x10000) % 0x400) + 0xdc00;
        result += '\\u' + high.toString(16).padStart(4, '0');
        result += '\\u' + low.toString(16).padStart(4, '0');
      }
    }
  }
  return result;
}

function processFile(filePath) {
  const src = fs.readFileSync(filePath, 'utf8');
  let out = '';
  let i = 0;
  const len = src.length;
  let state = 'normal'; // normal | slComment | mlComment | sQuote | dQuote | template

  while (i < len) {
    const ch = src[i];
    const next = src[i + 1];

    // STATE TRANSITIONS
    if (state === 'normal') {
      if (ch === '/' && next === '/') { // // comment
        out += ch + next;
        i += 2;
        state = 'slComment';
        continue;
      }
      if (ch === '/' && next === '*') { // /* comment */
        out += ch + next;
        i += 2;
        state = 'mlComment';
        continue;
      }
      if (ch === "'") { // single‑quote string
        out += ch;
        i++;
        state = 'sQuote';
        continue;
      }
      if (ch === '"') { // double‑quote string
        out += ch;
        i++;
        state = 'dQuote';
        continue;
      }
      if (ch === '`') { // template literal
        out += ch;
        i++;
        state = 'template';
        continue;
      }
      // default copy
      out += ch;
      i++;
      continue;
    }

    // SINGLE‑LINE COMMENT
    if (state === 'slComment') {
      if (ch === '\n') {
        out += ch;
        i++;
        state = 'normal';
        continue;
      }
      // replace comment chars on the fly
      out += replaceInComment(ch);
      i++;
      continue;
    }

    // MULTI‑LINE COMMENT
    if (state === 'mlComment') {
      if (ch === '*' && next === '/') {
        out += replaceInComment(ch) + replaceInComment(next);
        i += 2;
        state = 'normal';
        continue;
      }
      out += replaceInComment(ch);
      i++;
      continue;
    }

    // SINGLE‑QUOTE STRING
    if (state === 'sQuote') {
      if (ch === "\\") { // escape sequence – copy next char verbatim
        out += ch + (src[i + 1] || '');
        i += 2;
        continue;
      }
      if (ch === "'") {
        out += ch;
        i++;
        state = 'normal';
        continue;
      }
      out += replaceInString(ch);
      i++;
      continue;
    }

    // DOUBLE‑QUOTE STRING
    if (state === 'dQuote') {
      if (ch === "\\") {
        out += ch + (src[i + 1] || '');
        i += 2;
        continue;
      }
      if (ch === '"') {
        out += ch;
        i++;
        state = 'normal';
        continue;
      }
      out += replaceInString(ch);
      i++;
      continue;
    }

    // TEMPLATE LITERAL
    if (state === 'template') {
      if (ch === "\\") {
        out += ch + (src[i + 1] || '');
        i += 2;
        continue;
      }
      if (ch === '`') {
        out += ch;
        i++;
        state = 'normal';
        continue;
      }
      // handle ${ … } expressions – we just treat them as normal chars because they are JS code.
      if (ch === '$' && next === '{') {
        out += ch + next;
        i += 2;
        // enter an expression state that behaves like normal JS until the matching '}'
        let braceDepth = 1;
        while (i < len && braceDepth > 0) {
          const c = src[i];
          const n = src[i + 1];
          if (c === '{') braceDepth++;
          else if (c === '}') braceDepth--;
          out += c;
          i++;
        }
        continue;
      }
      out += replaceInString(ch);
      i++;
      continue;
    }
  }

  if (out !== src) {
    fs.writeFileSync(filePath, out, 'utf8');
    console.log('Sanitised', filePath);
  }
}

function walk(dir) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      // skip node_modules, .git, build artefacts
      if (['node_modules', '.git', 'dist', 'build'].includes(entry.name)) continue;
      walk(full);
    } else if (entry.isFile() && full.endsWith('.js')) {
      processFile(full);
    }
  }
}

const targetRoot = path.resolve(__dirname, '../frontend/src/js');
walk(targetRoot);

console.log('Sanitisation complete');
