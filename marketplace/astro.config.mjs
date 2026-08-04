// @ts-check
import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';

// https://astro.build/config
export default defineConfig({
  site: 'https://tonsofskills.com',
  base: '/',
  // NO Astro `redirects` here — deliberately. See /etc/caddy/tonsofskills-redirects.caddy
  // on the VPS, which serves all 84 as real HTTP 301s.
  //
  // Astro's redirects config emits one thin HTML page per entry containing
  // <meta http-equiv="refresh" content="0;url=...">. Adding 81 of them on
  // 2026-08-03 took the site from 3 to 85 instant-redirect pages in a single
  // deploy, and a consumer network-security filter began blocking
  // tonsofskills.com hours later. A mass of instant meta-refresh pages is the
  // classic doorway-page / cloaking signature those heuristics look for.
  //
  // Causation was never proven — Google Safe Browsing reported the domain clean
  // throughout — but meta-refresh is the wrong mechanism regardless: a permanent
  // redirect belongs in the HTTP status line, not in markup a crawler has to
  // execute. Real 301s are faster, keep 85 thin pages out of the crawl surface,
  // and pass link equity correctly.
  //
  // If you need a new redirect, add it to the Caddy file — NOT here.
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
