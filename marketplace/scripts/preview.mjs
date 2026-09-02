import { createServer } from 'node:http';
import { readFile, stat } from 'node:fs/promises';
import { extname, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

import { securityHeadersForPath } from './security-policy.mjs';

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

function safePath(root, pathname) {
  let decoded;
  try {
    decoded = decodeURIComponent(pathname);
  } catch {
    return null;
  }
  if (decoded.includes('\0') || decoded.includes('\\')) return null;

  const absoluteRoot = resolve(root);
  const candidate = resolve(absoluteRoot, decoded.replace(/^\/+/, '') || '.');
  if (candidate !== absoluteRoot && !candidate.startsWith(`${absoluteRoot}${sep}`)) return null;
  return candidate;
}

async function isFile(path) {
  try {
    return (await stat(path)).isFile();
  } catch (error) {
    if (error?.code === 'ENOENT' || error?.code === 'ENOTDIR') return false;
    throw error;
  }
}

export async function resolvePreviewAsset(root, pathname) {
  const base = safePath(root, pathname);
  if (!base) return null;

  const candidates = [base];
  if (!extname(base)) candidates.push(`${base}.html`);
  candidates.push(resolve(base, 'index.html'));

  for (const candidate of candidates) {
    if (await isFile(candidate)) return candidate;
  }
  return undefined;
}

export function createPreviewServer({ root = DEFAULT_ROOT } = {}) {
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

    let pathname;
    try {
      pathname = new URL(requestTarget, 'http://localhost').pathname;
    } catch {
      response.writeHead(400, { 'Content-Type': 'text/plain; charset=utf-8' });
      response.end('Bad Request\n');
      return;
    }

    try {
      const asset = await resolvePreviewAsset(root, pathname);
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
