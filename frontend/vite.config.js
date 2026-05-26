import { defineConfig } from 'vite';
import { resolve } from 'path';

export default defineConfig({
  publicDir: 'static',
  server: {
    port: 5173,
    host: '0.0.0.0',
    strictPort: true
  },
  build: {
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'index.html'),
        login: resolve(__dirname, 'login.html'),
        dashboard: resolve(__dirname, 'dashboard.html'),
        admin: resolve(__dirname, 'admin.html')
      },
      output: {
        // Split heavy libraries into separate chunks for lazy loading
        manualChunks: {
          chart: ['chart.js'],
          leaflet: ['leaflet']
        }
      }
    }
  }
});
