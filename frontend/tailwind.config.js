/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./login.html",
    "./dashboard.html",
    "./admin.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class', // Enable class-based dark mode
  theme: {
    extend: {
      colors: {
        /* ── Semantic Color System (responds to .light-mode class on <body>) ── */
        'mole-bg':    'var(--mole-bg, #0B0F19)',      /* Background */
        'mole-surface': 'var(--mole-surface, #111827)',  /* Cards/panels */
        'mole-border': 'var(--mole-border, #1E293B)',   /* Borders */
        'mole-text':  'var(--mole-text, #00E5FF)',      /* Primary text (WCAG AA: 4.5:1 contrast) */
        'mole-text-dim': 'var(--mole-text-dim, #94A3B8)', /* Muted text */
        'mole-accent': 'var(--mole-accent, #00E5FF)',   /* Accent (Pip-Boy cyan) */
        'mole-green':  'var(--mole-green, #34D399)',     /* Success */
        'mole-amber':  'var(--mole-amber, #FBBF24)',     /* Warning */
        'mole-red':    'var(--mole-red, #F87171)',       /* Error */
        'mole-cyan':   '#00E5FF',                         /* Keep original for backward compat */
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
