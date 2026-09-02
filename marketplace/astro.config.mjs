// @ts-check
import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';

import { MARKETPLACE_SECURITY_HEADERS } from './scripts/security-policy.mjs';

// https://astro.build/config
export default defineConfig({
  site: 'https://tonsofskills.com',
  base: '/',
  // NO Astro `redirects` here — deliberately. See /etc/caddy/tonsofskills-redirects.caddy
  // on the VPS, which serves the generated redirect inventory as real HTTP 301s.
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
  // execute. Real 301s are faster, keep those thin pages out of the crawl surface,
  // and pass link equity correctly.
  //
  // If you need a new redirect, add it to the Caddy file — NOT here.

  // EXCEPTION — these three predate the 2026-08-03 404-repair work and stay in
  // Astro. scripts/check-routes.mjs treats them as real routes and asserts the
  // built files exist, so moving them to Caddy breaks that gate. Three redirect
  // pages is also not the doorway-page pattern the move was about; eighty-one
  // was. Keeping them here means one source of truth per redirect.
  redirects: {
    '/learning/built-system-summary': '/learning/',
    '/learning/getting-started': '/learning/overview/',
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
    // Preview must enforce the same policy as production Caddy. This also
    // makes browser tests exercise a real response header rather than a meta
    // tag that browsers may ignore.
    server: { headers: MARKETPLACE_SECURITY_HEADERS },
    preview: { headers: MARKETPLACE_SECURITY_HEADERS },
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
