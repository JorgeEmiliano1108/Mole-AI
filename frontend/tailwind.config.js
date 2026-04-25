/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./login.html",
    "./dashboard.html",
    "./admin.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        /* ── Cyber-Agrícola Palette ──────────────────────────── */
        'mole-base':    '#0B0F19',  /* Deep night blue — base background */
        'mole-surface': '#111827',  /* Slate-900 — card/panel surfaces */
        'mole-border':  '#1E293B',  /* Slate-800 — subtle borders */
        'mole-cyan':    '#00E5FF',  /* Primary accent (desaturated cyan) */
        'mole-green':   '#34D399',  /* Emerald-400 — success / health */
        'mole-amber':   '#FBBF24',  /* Amber-400 — warnings / legal */
        'mole-red':     '#F87171',  /* Red-400 — errors / critical */
        'mole-dim':     '#94A3B8',  /* Slate-400 — muted text */
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'Consolas', 'monospace'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
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
