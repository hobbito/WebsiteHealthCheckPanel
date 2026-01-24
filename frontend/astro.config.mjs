import { defineConfig } from 'astro/config';
import react from '@astrojs/react';
import tailwind from '@astrojs/tailwind';

export default defineConfig({
  integrations: [
    react(),
    tailwind()
  ],
  output: 'hybrid',
  server: {
    port: 3000,
    host: true
  },
  vite: {
    server: {
      proxy: {
        '/api': {
          target: process.env.PUBLIC_API_URL || 'http://localhost:8000',
          changeOrigin: true
        }
      }
    }
  }
});
