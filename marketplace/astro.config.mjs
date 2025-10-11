// @ts-check
import { defineConfig } from 'astro/config';

import tailwindcss from '@tailwindcss/vite';

// https://astro.build/config
export default defineConfig({
  site: 'https://jeremylongshore.github.io',
  base: '/claude-code-plugins',
  vite: {
    plugins: [tailwindcss()]
  }
});