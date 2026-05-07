/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./*.html",
    "./src/**/*.{js,ts,jsx,tsx,css}",
  ],
  darkMode: 'class', // Enable class-based dark mode
  theme: {
    extend: {
  colors: {
    /* ── Semantic Color System (responds to .light-mode class on <body>) ── */
    'mole-bg':    'var(--mole-bg, #0B0F19)',        /* Background */
    'mole-surface': 'var(--mole-surface, #111827)',  /* Cards/panels */
    'mole-border': 'var(--mole-border, #1E293B)',    /* Borders */
    'mole-text':  'var(--mole-text, #00FFCC)',       /* Primary text (WCAG AA: 5.5:1 contrast on #0B0F19) */
    'mole-text-dim': 'var(--mole-text-dim, #94A3B8)', /* Muted text */
    'mole-accent': 'var(--mole-accent, #00FFCC)',    /* Accent (Pip-Boy cyan - brighter for readability) */
    'mole-green':  'var(--mole-green, #34D399)',     /* Success */
    'mole-amber':  'var(--mole-amber, #FBBF24)',     /* Warning */
    'mole-red':    'var(--mole-red, #F87171)',       /* Error */
    'mole-cyan':   '#00FFCC',                         /* Updated: brighter cyan for terminal/chat */
    /* ── CMD CENTER Industrial Theme ── */
    'mole-bg-alt': 'var(--mole-bg-alt, #05080A)',          /* Alt Background (#05080a or #0b0f13) */
    'mole-surface-industrial': 'var(--mole-surface-industrial, #111820)', /* Industrial surface */
    'mole-border-industrial': 'var(--mole-border-industrial, #1A2E26)', /* Solid 1px borders */
    'mole-critical': '#FF4D4D',                        /* Critical alerts */
    'mole-warning': '#FFCC00',                         /* Warning alerts */
  },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],       /* DEFAULT for body text */
        display: ['"Montserrat"', 'sans-serif'],          /* For titles */
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'Consolas', 'monospace'],
        terminal: ['VT323', 'monospace'],                 /* ONLY for chat/terminal */
      },
      boxShadow: {
        'cyber': '0 0 15px rgba(0, 229, 255, 0.08)',
        'cyber-hover': '0 0 25px rgba(0, 229, 255, 0.15)',
        'glow': '0 0 10px rgba(0, 255, 204, 0.2)',
      },
      animation: {
        'cursor-blink': 'blink 1s step-end infinite',
      },
      keyframes: {
        blink: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0' },
        },
      },
    },
  },
  plugins: [],
}
