// @ts-check
import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';

// https://astro.build/config
export default defineConfig({
  site: 'https://claudecodeplugins.io',
  base: '/',
  build: {
    assets: '_astro',
    inlineStylesheets: 'auto'
  },
  output: 'static',
  compressHTML: false,  // Disabled: iOS Safari can't handle extremely long lines from aggressive minification
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
