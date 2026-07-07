import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: [],
  },
  server: {
    watch: {
      ignored: ['**/dist/**'],
    },
  },
});
