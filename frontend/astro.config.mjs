import { defineConfig } from 'astro/config';
import react from '@astrojs/react';
import tailwind from '@astrojs/tailwind';
import vercel from '@astrojs/vercel/serverless';

export default defineConfig({
  integrations: [
    react(),
    tailwind()
  ],
  output: 'server',
  adapter: vercel({
    webAnalytics: { enabled: false }
  }),
  server: {
    port: 3000,
    host: true
  },
  vite: {
    define: {
      'import.meta.env.PUBLIC_API_URL': JSON.stringify(process.env.PUBLIC_API_URL || '')
    }
  }
});
