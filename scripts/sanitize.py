#!/usr/bin/env python3
"""
sanitize.py – clean non‑ASCII characters from JS source files.

The script walks frontend/src/js recursively and for each *.js file it:
* Replaces any non‑ASCII character inside comments (// … or /* … */) with a suitable ASCII fallback (dash, arrow, space).
* Replaces any non‑ASCII character inside string literals (single, double, template) with a Unicode escape (e.g. \u00E1) so that the runtime UI text remains unchanged.

It overwrites the file only when a modification occurs and prints the path of every changed file.
"""
import os
import re
import sys

# Mapping for common punctuation that appears in comments.
COMMENT_MAP = {
    "–": "-",  # EN DASH
    "—": "-",  # EM DASH
    "→": "->",
    "←": "<-",
    "↑": "^",
    "↓": "v",
    "•": "-",
    "\u00A0": " ",   # NO‑BREAK SPACE
    "\u202F": " ",   # NARROW NO‑BREAK SPACE
    "\u2009": " ",   # THIN SPACE
    "\u2003": " ",   # EM SPACE
}

def replace_comment(text: str) -> str:
    """Replace non‑ASCII characters in a comment string.
    Unknown characters are converted to a single space.
    """
    out = []
    for ch in text:
        if ord(ch) <= 0x7f:
            out.append(ch)
        elif ch in COMMENT_MAP:
            out.append(COMMENT_MAP[ch])
        else:
            out.append(' ')
    return ''.join(out)

def escape_string(text: str) -> str:
    """Replace non‑ASCII characters in a JS string literal with a Unicode escape (e.g. \\u00E1).
    Escape sequences (\\n, \\" , etc.) are left untouched because they are already ASCII.
    """
    out = []
    i = 0
    while i < len(text):
        ch = text[i]
        code = ord(ch)
        if code <= 0x7f:
            out.append(ch)
        else:
            # Encode as \uXXXX (or surrogate pair if > 0xFFFF)
            cp = ord(ch)
            if cp <= 0xFFFF:
                out.append('\\u{:04x}'.format(cp))
            else:
                # Encode as UTF‑16 surrogate pair
                cp -= 0x10000
                high = 0xD800 + (cp >> 10)
                low = 0xDC00 + (cp & 0x3FF)
                out.append('\\u{:04x}\\u{:04x}'.format(high, low))
        i += 1
    return ''.join(out)

# Regular expressions to locate comments and string literals.
# Comments (single‑line // …) and multi‑line /* … */ are captured.
COMMENT_RE = re.compile(r"//.*?$|/\*.*?\*/", re.DOTALL | re.MULTILINE)
# String literals – single, double, or back‑ticks. Handles escaped quotes.
STRING_RE = re.compile(r"('(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\"|`(?:\\.|[^`\\])*`)", re.DOTALL)

def process_file(path: str) -> bool:
    with open(path, 'r', encoding='utf-8') as f:
        source = f.read()
    original = source

    # First, fix comments.
    def comment_sub(m):
        return replace_comment(m.group(0))
    source = COMMENT_RE.sub(comment_sub, source)

    # Then, fix string literals.
    def string_sub(m):
        lit = m.group(0)
        # Preserve the surrounding quotes/backticks.
        quote = lit[0]
        inner = lit[1:-1]
        return quote + escape_string(inner) + quote
    source = STRING_RE.sub(string_sub, source)

    if source != original:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(source)
        print('sanitised', path)
        return True
    return False

def walk(dir_path: str):
    for root, dirs, files in os.walk(dir_path):
        # Skip noisy directories.
        dirs[:] = [d for d in dirs if d not in ('node_modules', '.git', 'dist', 'build')]
        for name in files:
            if name.endswith('.js'):
                full = os.path.join(root, name)
                process_file(full)

if __name__ == '__main__':
    target = os.path.abspath(os.path.join(os.path.dirname(__file__), '../frontend/src/js'))
    walk(target)
    sys.exit(0)
