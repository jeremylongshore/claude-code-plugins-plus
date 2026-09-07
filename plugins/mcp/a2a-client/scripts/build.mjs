import { chmod, readFile, writeFile } from 'node:fs/promises';
import { fileURLToPath, URL } from 'node:url';
import { build } from 'esbuild';

const outfile = fileURLToPath(new URL('../dist/index.js', import.meta.url));

await build({
  entryPoints: [fileURLToPath(new URL('../src/index.ts', import.meta.url))],
  bundle: true,
  platform: 'node',
  format: 'esm',
  target: 'node20',
  minify: true,
  legalComments: 'eof',
  outfile,
  banner: {
    js: "import { createRequire } from 'node:module'; const require = createRequire(import.meta.url);",
  },
});

// Third-party bundled source can contain whitespace-only lines. Normalize the
// deterministic publication artifact so the repository's diff gate stays clean.
const bundled = await readFile(outfile, 'utf8');
await writeFile(outfile, bundled.replace(/[\t ]+$/gm, ''));
await chmod(outfile, 0o755);
