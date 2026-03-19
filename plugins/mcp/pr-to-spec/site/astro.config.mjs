// @ts-check
import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  site: 'https://jeremylongshore.github.io',
  base: '/pr-to-prompt/',
  output: 'static',
  vite: {
    plugins: [tailwindcss()],
  },
});
