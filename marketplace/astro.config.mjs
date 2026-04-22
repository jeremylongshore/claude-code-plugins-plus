// @ts-check
import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';

// https://astro.build/config
export default defineConfig({
  site: 'https://tonsofskills.com',
  base: '/',
  redirects: {
    // Fix 404s from deleted Learning Lab pages (Jan 2026)
    '/learning/built-system-summary': '/learning/',
    '/learning/getting-started': '/learning/overview/',
    // Spotlight page retired 2026-04-22 — Hall of Fame lives on /community.
    '/spotlight': '/community#hall-of-fame',
  },
  build: {
    assets: '_astro',
    inlineStylesheets: 'auto'
  },
  output: 'static',
  compressHTML: false,  // Disabled: iOS Safari fails with lines > 5000 chars
  vite: {
    plugins: [tailwindcss()],
    build: {
      cssCodeSplit: true,
      rollupOptions: {
        output: {
          assetFileNames: '_astro/[name].[hash][extname]'
        }
      }
    }
  }
});
