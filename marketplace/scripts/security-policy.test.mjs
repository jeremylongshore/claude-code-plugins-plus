import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

import { renderCaddyHeaders } from './render-security-headers-caddy.mjs';
import {
  CSP_DIRECTIVES,
  CSP_INLINE_JUSTIFICATIONS,
  MARKETPLACE_SECURITY_HEADERS,
  serializeCsp,
  validateSecurityPolicy,
} from './security-policy.mjs';

const caddyPath = new URL('../ops/tonsofskills-security-headers.caddy', import.meta.url);

test('policy fails closed on the high-value XSS boundaries', () => {
  const policy = serializeCsp();
  assert.match(policy, /default-src 'self'/);
  assert.match(policy, /object-src 'none'/);
  assert.match(policy, /base-uri 'self'/);
  assert.match(policy, /frame-ancestors 'self'/);
  assert.match(policy, /form-action 'self'/);
  assert.doesNotMatch(policy, /unsafe-eval/);
  assert.doesNotMatch(policy, /(?:^|\s)\*(?:\s|;|$)/);
  assert.equal(MARKETPLACE_SECURITY_HEADERS['X-Content-Type-Options'], 'nosniff');
});

test('every inline exception is explicit and justified', () => {
  for (const [directive, values] of Object.entries(CSP_DIRECTIVES)) {
    if (!values.includes("'unsafe-inline'")) continue;
    assert.ok(CSP_INLINE_JUSTIFICATIONS[directive], `${directive} needs a justification`);
  }
  assert.deepEqual(Object.keys(CSP_INLINE_JUSTIFICATIONS).sort(), [
    'script-src',
    'style-src',
  ]);
});

test('tracked Caddy fragment is an exact projection of the preview policy', () => {
  assert.equal(readFileSync(caddyPath, 'utf8'), renderCaddyHeaders());
});

test('planted weakening is rejected by the policy assertions', () => {
  const missingBoundary = structuredClone(CSP_DIRECTIVES);
  delete missingBoundary['object-src'];
  assert.throws(() => validateSecurityPolicy(missingBoundary), /object-src/);

  const executableString = structuredClone(CSP_DIRECTIVES);
  executableString['script-src'] = [...executableString['script-src'], "'unsafe-eval'"];
  assert.throws(() => validateSecurityPolicy(executableString), /unsafe-eval/);

  const wildcard = structuredClone(CSP_DIRECTIVES);
  wildcard['connect-src'] = [...wildcard['connect-src'], '*'];
  assert.throws(() => validateSecurityPolicy(wildcard), /wildcard/);

  assert.throws(
    () => validateSecurityPolicy(CSP_DIRECTIVES, { 'style-src': 'only one exception' }),
    /script-src unsafe-inline requires/,
  );
});
