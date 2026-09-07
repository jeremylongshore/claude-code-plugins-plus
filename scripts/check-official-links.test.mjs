import test from 'node:test';
import assert from 'node:assert/strict';
import {
  isDevelopmentHostnameAllowed,
  isDevelopmentUrlAllowed,
  isDomainBlocked,
  isLinkAllowed,
} from './check-official-links.mjs';

function assertDevelopmentAllowed(url) {
  assert.deepEqual(isDevelopmentUrlAllowed(url), { allowed: true, reason: 'development' });
}

function assertDevelopmentRejected(url, reason = 'not-development-host') {
  assert.deepEqual(isDevelopmentUrlAllowed(url), { allowed: false, reason });
}

test('allows intended development hosts with valid ports and paths', () => {
  for (const url of [
    'http://localhost:3000/health?ready=1#top',
    "http://localhost:5678',",
    'http://127.0.0.1:7847`',
    "https://example.com'];",
    'https://127.0.0.1:8443/api',
    'http://0.0.0.0:8080/',
    'https://[::1]:3000/app',
    'https://printer.local:9443/status',
    'https://office.printer.local/devices',
    'https://example.com:65535/docs',
    'https://docs.example.com/reference',
    'https://LOCALHOST.:3000/health',
    'https://docs.example.com./reference',
  ]) {
    assertDevelopmentAllowed(url);
  }
});

test('uses exact hostname and subdomain boundaries', () => {
  for (const hostname of [
    'localhost.example.test',
    '127.0.0.10',
    '0.0.0.0.example.test',
    'printer.local.example.test',
    'example.com.example.test',
    'notexample.com',
    'example.com.evil.test',
  ]) {
    assert.equal(isDevelopmentHostnameAllowed(hostname), false, hostname);
  }

  for (const url of [
    'https://localhost.example.test/path',
    'https://127.0.0.10:3000/',
    'https://printer.local.example.test/status',
    'https://example.com.evil.test/docs',
  ]) {
    assertDevelopmentRejected(url);
  }
});

test('normalizes trailing dots without weakening future blocklist boundaries', () => {
  assert.equal(isDomainBlocked('BAD.EXAMPLE.', ['bad.example']), true);
  assert.equal(isDomainBlocked('child.bad.example.', ['bad.example.']), true);
  assert.equal(isDomainBlocked('notbad.example.', ['bad.example']), false);
  assert.equal(isDomainBlocked('bad.example.evil.', ['bad.example']), false);
});

test('rejects credentials even when the parsed hostname would otherwise be allowed', () => {
  for (const url of [
    'https://evil.example@localhost:3000/path',
    'https://user:password@example.com/docs',
    'https://localhost@evil.test/path',
  ]) {
    assertDevelopmentRejected(url, 'credentials');
    assert.deepEqual(isLinkAllowed(url), { allowed: false, reason: 'credentials' });
  }
});

test('preserves placeholder URL behavior without treating malformed URLs as development hosts', () => {
  assertDevelopmentAllowed('https://api.[REGION].example.com/v1');
  assertDevelopmentAllowed('https://github.com/[PROJECT]/issues');
  assertDevelopmentAllowed(
    'https://[REGION]-[PROJECT_ID].cloudfunctions.net/export?project=[PROJECT_ID]',
  );
  assertDevelopmentRejected('https://api.test/not-a-placeholder');
  assertDevelopmentRejected('https://evil.test:bad/[PROJECT]', 'invalid-url');
  assertDevelopmentRejected('https://evil@[REGION].example.com/path', 'credentials');
  assertDevelopmentRejected('https://user:pass@localhost:bad/[PROJECT]', 'invalid-url');
  assertDevelopmentRejected('https://example.test/[PROJECT', 'not-development-host');
});

test('the public validator remains an explicit blocklist policy', () => {
  assertDevelopmentRejected('https://localhost.example.test/path');
  assert.deepEqual(isLinkAllowed('https://localhost.example.test/path'), {
    allowed: true,
    reason: 'default-allow',
  });
});

test('rejects invalid ports instead of treating them as development URLs', () => {
  assert.deepEqual(isDevelopmentUrlAllowed('https://localhost:99999/path'), {
    allowed: false,
    reason: 'invalid-url',
  });
  assert.deepEqual(isLinkAllowed('https://localhost:99999/path'), {
    allowed: false,
    reason: 'invalid-url',
    error: 'Invalid URL',
  });
});

test('importing the validator does not execute the repository scan', () => {
  assert.equal(typeof isLinkAllowed, 'function');
});
