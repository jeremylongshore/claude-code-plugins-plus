import assert from 'node:assert/strict';
import { mkdir, mkdtemp, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';

import { createPreviewServer, resolvePreviewAsset } from './preview.mjs';
import { MARKETPLACE_CHAT_SECURITY_HEADERS, MARKETPLACE_SECURITY_HEADERS } from './security-policy.mjs';

async function fixture(t) {
  const parent = await mkdtemp(join(tmpdir(), 'marketplace-preview-'));
  const root = join(parent, 'dist');
  await mkdir(join(root, 'chats'), { recursive: true });
  await mkdir(join(root, '_astro'), { recursive: true });
  await writeFile(join(root, 'index.html'), '<h1>home</h1>');
  await writeFile(join(root, 'chats', 'index.html'), '<h1>chat</h1>');
  await writeFile(join(root, '_astro', 'app.js'), 'export const ok = true;');
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
  return { base: `http://127.0.0.1:${address.port}`, root };
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
  assert.equal(await resolvePreviewAsset(root, '/%2e%2e%2fsecret.txt'), null);

  const traversal = await fetch(`${base}/%2e%2e%2fsecret.txt`);
  assert.equal(traversal.status, 400);
  assert.notEqual(await traversal.text(), 'must not escape root');

  const malformed = await fetch(`${base}/%E0%A4%A`);
  assert.equal(malformed.status, 400);

  const post = await fetch(`${base}/`, { method: 'POST' });
  assert.equal(post.status, 405);
  assert.equal(post.headers.get('allow'), 'GET, HEAD');
});
