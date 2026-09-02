import assert from 'node:assert/strict';
import { mkdir, mkdtemp, rm, symlink, unlink, writeFile } from 'node:fs/promises';
import { connect } from 'node:net';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';

import {
  buildPreviewAssetIndex,
  createPreviewServer,
  resolvePreviewAsset,
} from './preview.mjs';
import {
  MARKETPLACE_CHAT_SECURITY_HEADERS,
  MARKETPLACE_SECURITY_HEADERS,
  normalizeRequestPath,
} from './security-policy.mjs';

async function fixture(t) {
  const parent = await mkdtemp(join(tmpdir(), 'marketplace-preview-'));
  const root = join(parent, 'dist');
  await mkdir(join(root, 'chats'), { recursive: true });
  await mkdir(join(root, '_astro'), { recursive: true });
  await writeFile(join(root, 'index.html'), '<h1>home</h1>');
  await writeFile(join(root, 'chats', 'index.html'), '<h1>chat</h1>');
  await writeFile(join(root, '_astro', 'app.js'), 'export const ok = true;');
  await writeFile(join(root, 'public.txt'), 'public snapshot');
  await writeFile(join(parent, 'secret.txt'), 'must not escape root');

  const server = createPreviewServer({ root });
  await new Promise((accept, reject) => {
    server.once('error', reject);
    server.listen(0, '127.0.0.1', accept);
  });
  t.after(async () => {
    await new Promise((accept, reject) =>
      server.close((error) => (error ? reject(error) : accept())),
    );
    await rm(parent, { recursive: true, force: true });
  });
  const address = server.address();
  assert.ok(address && typeof address === 'object');
  return { base: `http://127.0.0.1:${address.port}`, port: address.port, root };
}

async function rawRequest(port, request) {
  return await new Promise((accept, reject) => {
    const socket = connect(port, '127.0.0.1');
    let response = '';
    socket.setEncoding('utf8');
    socket.once('error', reject);
    socket.on('data', (chunk) => {
      response += chunk;
    });
    socket.on('end', () => accept(response));
    socket.on('connect', () => socket.write(request));
  });
}

function rawHeader(response, name) {
  const prefix = `${name.toLowerCase()}:`;
  const line = response
    .split('\r\n')
    .find((candidate) => candidate.toLowerCase().startsWith(prefix));
  return line?.slice(prefix.length).trim();
}

test('serves built pages with exact route-aware security headers', async (t) => {
  const { base } = await fixture(t);
  const root = await fetch(`${base}/`);
  assert.equal(root.status, 200);
  assert.equal(await root.text(), '<h1>home</h1>');
  assert.equal(root.headers.get('content-security-policy'), MARKETPLACE_SECURITY_HEADERS['Content-Security-Policy']);
  assert.equal(root.headers.get('permissions-policy'), MARKETPLACE_SECURITY_HEADERS['Permissions-Policy']);

  const chat = await fetch(`${base}/chats/`);
  assert.equal(chat.status, 200);
  assert.equal(chat.headers.get('content-security-policy'), MARKETPLACE_CHAT_SECURITY_HEADERS['Content-Security-Policy']);
  assert.match(chat.headers.get('content-security-policy'), /(?:^|\s)wss:/);
  assert.doesNotMatch(root.headers.get('content-security-policy'), /(?:^|\s)wss?:/);
});

test('serves static assets and HEAD requests with correct metadata', async (t) => {
  const { base } = await fixture(t);
  const asset = await fetch(`${base}/_astro/app.js`);
  assert.equal(asset.status, 200);
  assert.equal(asset.headers.get('content-type'), 'text/javascript; charset=utf-8');

  const head = await fetch(`${base}/`, { method: 'HEAD' });
  assert.equal(head.status, 200);
  assert.equal(head.headers.get('content-length'), String(Buffer.byteLength('<h1>home</h1>')));
  assert.equal(await head.text(), '');
});

test('fails closed on traversal, malformed paths, and unsupported methods', async (t) => {
  const { base, root } = await fixture(t);
  const index = await buildPreviewAssetIndex(root);
  assert.equal(
    resolvePreviewAsset(index, normalizeRequestPath('/%2e%2e%2fsecret.txt')),
    undefined,
  );

  const traversal = await fetch(`${base}/%2e%2e%2fsecret.txt`);
  assert.equal(traversal.status, 404);
  assert.notEqual(await traversal.text(), 'must not escape root');

  const malformed = await fetch(`${base}/%E0%A4%A`);
  assert.equal(malformed.status, 400);

  const post = await fetch(`${base}/`, { method: 'POST' });
  assert.equal(post.status, 405);
  assert.equal(post.headers.get('allow'), 'GET, HEAD');
});

test('rejects malformed and ambiguous request targets without crashing', async (t) => {
  const { base, port } = await fixture(t);
  const malformed = await rawRequest(
    port,
    'GET http://[ HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n',
  );
  assert.match(malformed, /^HTTP\/1\.1 400 Bad Request/m);

  const ambiguous = await rawRequest(
    port,
    'GET //evil.invalid/chats HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n',
  );
  assert.match(ambiguous, /^HTTP\/1\.1 400 Bad Request/m);
  assert.equal(
    rawHeader(ambiguous, 'content-security-policy'),
    MARKETPLACE_SECURITY_HEADERS['Content-Security-Policy'],
  );

  const after = await fetch(`${base}/`);
  assert.equal(after.status, 200);
});

test('normalizes encoded chat paths to the same route policy used by Caddy', async (t) => {
  const { base } = await fixture(t);
  const response = await fetch(`${base}/%63hats/`);
  assert.equal(response.status, 200);
  assert.equal(
    response.headers.get('content-security-policy'),
    MARKETPLACE_CHAT_SECURITY_HEADERS['Content-Security-Policy'],
  );
});

test('refuses symlinks that resolve outside the configured build root', async (t) => {
  const { base, root } = await fixture(t);
  await symlink('../secret.txt', join(root, 'exposed.txt'));

  const response = await fetch(`${base}/exposed.txt`);
  assert.equal(response.status, 400);
  assert.notEqual(await response.text(), 'must not escape root');
});

test('serves an immutable snapshot after an indexed file is swapped for an outside symlink', async (t) => {
  const { base, root } = await fixture(t);
  const before = await fetch(`${base}/public.txt`);
  assert.equal(before.status, 200);
  assert.equal(await before.text(), 'public snapshot');

  await unlink(join(root, 'public.txt'));
  await symlink('../secret.txt', join(root, 'public.txt'));

  const after = await fetch(`${base}/public.txt`);
  assert.equal(after.status, 200);
  assert.equal(await after.text(), 'public snapshot');
});

test('collapses dot-segment chat aliases before policy and asset selection', async (t) => {
  const { port } = await fixture(t);
  for (const requestTarget of ['/chats/../', '/chats/%2e%2e/', '/chats/../index.html']) {
    const response = await rawRequest(
      port,
      `GET ${requestTarget} HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n`,
    );
    assert.match(response, /^HTTP\/1\.1 200 OK/m);
    assert.equal(
      rawHeader(response, 'content-security-policy'),
      MARKETPLACE_SECURITY_HEADERS['Content-Security-Policy'],
    );
    assert.match(response, /<h1>home<\/h1>/);
  }
});
