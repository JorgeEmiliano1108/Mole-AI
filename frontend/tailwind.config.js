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
        'mole-green': '#00ffaa',
        'mole-dark': '#0a0a0a',
      },
      fontFamily: {
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
      },
      animation: {
        'biometric-scan': 'biometric-scan 2.5s cubic-bezier(0.4, 0, 0.2, 1) infinite',
      },
      keyframes: {
        'biometric-scan': {
          '0%': { top: '-5%', opacity: '0' },
          '5%': { opacity: '0.8' },
          '95%': { opacity: '0.8' },
          '100%': { top: '105%', opacity: '0' },
        },
      },
    },
  },
  plugins: [],
}
