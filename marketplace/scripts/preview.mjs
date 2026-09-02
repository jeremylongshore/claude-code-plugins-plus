import { createServer } from 'node:http';
import { readFile, readdir, realpath } from 'node:fs/promises';
import { extname, relative, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

import { normalizeRequestPath, securityHeadersForPath } from './security-policy.mjs';

const DEFAULT_ROOT = fileURLToPath(new URL('../dist/', import.meta.url));
const CONTENT_TYPES = Object.freeze({
  '.css': 'text/css; charset=utf-8',
  '.gif': 'image/gif',
  '.html': 'text/html; charset=utf-8',
  '.ico': 'image/x-icon',
  '.jpeg': 'image/jpeg',
  '.jpg': 'image/jpeg',
  '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8',
  '.png': 'image/png',
  '.svg': 'image/svg+xml; charset=utf-8',
  '.txt': 'text/plain; charset=utf-8',
  '.webmanifest': 'application/manifest+json; charset=utf-8',
  '.webp': 'image/webp',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2',
  '.xml': 'application/xml; charset=utf-8',
  '.zip': 'application/zip',
});

export async function buildPreviewAssetIndex(root) {
  const canonicalRoot = await realpath(root);
  const files = new Map();
  const symlinks = new Set();

  async function walk(directory) {
    const entries = await readdir(directory, { withFileTypes: true });
    await Promise.all(
      entries.map(async (entry) => {
        const absolutePath = resolve(directory, entry.name);
        const relativePath = relative(canonicalRoot, absolutePath).split(sep).join('/');
        if (entry.isSymbolicLink()) {
          symlinks.add(relativePath);
          return;
        }
        if (entry.isDirectory()) {
          await walk(absolutePath);
          return;
        }
        if (entry.isFile()) files.set(relativePath, absolutePath);
      }),
    );
  }

  await walk(canonicalRoot);
  return { files, symlinks };
}

export function resolvePreviewAsset(index, pathname) {
  const base = pathname.replace(/^\/+/, '');
  const candidates = [base];
  if (!extname(base)) candidates.push(`${base}.html`);
  candidates.push(base ? `${base.replace(/\/$/u, '')}/index.html` : 'index.html');

  for (const candidate of candidates) {
    if (index.symlinks.has(candidate)) return null;
    const asset = index.files.get(candidate);
    if (asset) return asset;
  }
  return undefined;
}

export function createPreviewServer({ root = DEFAULT_ROOT } = {}) {
  let assetIndexPromise;
  const getAssetIndex = () => {
    assetIndexPromise ??= buildPreviewAssetIndex(root);
    return assetIndexPromise;
  };

  return createServer(async (request, response) => {
    const requestTarget = request.url ?? '/';
    for (const [name, value] of Object.entries(securityHeadersForPath(requestTarget))) {
      response.setHeader(name, value);
    }
    response.setHeader('Cache-Control', 'no-store');

    if (request.method !== 'GET' && request.method !== 'HEAD') {
      response.writeHead(405, { Allow: 'GET, HEAD', 'Content-Type': 'text/plain; charset=utf-8' });
      response.end('Method Not Allowed\n');
      return;
    }

    const pathname = normalizeRequestPath(requestTarget);
    if (pathname === null) {
      response.writeHead(400, { 'Content-Type': 'text/plain; charset=utf-8' });
      response.end('Bad Request\n');
      return;
    }

    try {
      const asset = resolvePreviewAsset(await getAssetIndex(), pathname);
      if (asset === null) {
        response.writeHead(400, { 'Content-Type': 'text/plain; charset=utf-8' });
        response.end('Bad Request\n');
        return;
      }
      if (asset === undefined) {
        response.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
        response.end('Not Found\n');
        return;
      }

      const body = await readFile(asset);
      response.writeHead(200, {
        'Content-Length': String(body.byteLength),
        'Content-Type': CONTENT_TYPES[extname(asset).toLowerCase()] ?? 'application/octet-stream',
      });
      response.end(request.method === 'HEAD' ? undefined : body);
    } catch (error) {
      console.error(error);
      response.writeHead(500, { 'Content-Type': 'text/plain; charset=utf-8' });
      response.end('Internal Server Error\n');
    }
  });
}

const invokedPath = process.argv[1] ? resolve(process.argv[1]) : '';
if (invokedPath === fileURLToPath(import.meta.url)) {
  const host = process.env.HOST || '127.0.0.1';
  const port = Number.parseInt(process.env.PORT || '4321', 10);
  if (!Number.isInteger(port) || port < 1 || port > 65535) {
    throw new Error(`Invalid preview port: ${process.env.PORT}`);
  }
  const server = createPreviewServer();
  server.listen(port, host, () => {
    console.log(`Marketplace preview listening on http://${host}:${port}`);
  });
}
