#!/usr/bin/env node
/**
 * check-security-headers.mjs — assert the LIVE site sends its security headers.
 *
 * WHY THIS EXISTS
 * ---------------
 * `BaseLayout.astro` used to declare X-Frame-Options and X-Content-Type-Options
 * as `<meta http-equiv>`. Browsers ignore both in <meta> — they are
 * response-header-only — so the site had no clickjacking or MIME-sniffing
 * protection at all while appearing to have both. It survived indefinitely
 * because nothing checked the thing that actually matters: what the SERVER
 * sends. A source-code grep would have found the tags and concluded "handled".
 *
 * So this checks the response, not the markup. It is the generalisable lesson
 * from that bug — a control is only real if you verify it at the layer that
 * enforces it.
 *
 * The exact CSP is tracked in marketplace/scripts/security-policy.mjs and
 * projected into both Astro preview and the production Caddy fragment.
 *
 * USAGE
 *   node scripts/check-security-headers.mjs
 *   node scripts/check-security-headers.mjs --url https://staging.example.com
 *   node scripts/check-security-headers.mjs --warn-only   # report, exit 0
 *
 * Install with marketplace/ops/install-security-headers.sh; it validates a
 * complete candidate before changing Caddy and retains rollback backups.
 */

import { MARKETPLACE_SECURITY_HEADERS } from '../marketplace/scripts/security-policy.mjs';

const args = process.argv.slice(2);
const urlArg = args.indexOf('--url');
const URL_ = urlArg !== -1 ? args[urlArg + 1] : 'https://tonsofskills.com/';
const WARN_ONLY = args.includes('--warn-only');

// HSTS remains advisory for non-TLS local fixtures; every browser-enforced
// content boundary is required.
const EXPECT = [
  {
    name: 'content-security-policy',
    match: (value) => value === MARKETPLACE_SECURITY_HEADERS['Content-Security-Policy'],
    required: true,
  },
  { name: 'x-frame-options', match: /^(sameorigin|deny)$/i, required: true },
  { name: 'x-content-type-options', match: /^nosniff$/i, required: true },
  { name: 'referrer-policy', match: /.+/, required: true },
  { name: 'strict-transport-security', match: /max-age=\d+/i, required: false },
  { name: 'permissions-policy', match: /.+/, required: true },
];

let res;
try {
  res = await fetch(URL_, { method: 'HEAD', redirect: 'follow' });
} catch (e) {
  console.error(`FETCH FAILED: ${URL_} — ${e.message}`);
  process.exit(WARN_ONLY ? 0 : 1);
}

console.log(`security headers on ${URL_}  (HTTP ${res.status})\n`);
let missingRequired = 0;
for (const h of EXPECT) {
  const v = res.headers.get(h.name);
  const ok = v != null && (typeof h.match === 'function' ? h.match(v) : h.match.test(v));
  const tag = ok ? 'OK  ' : h.required ? 'FAIL' : 'warn';
  if (!ok && h.required) missingRequired++;
  console.log(`  ${tag}  ${h.name.padEnd(28)} ${v ?? '(absent)'}`);
}

if (missingRequired) {
  console.error(
    `\n${missingRequired} required security header(s) missing.\n` +
      `These CANNOT be set from HTML — a <meta http-equiv> tag is ignored by browsers.\n` +
      `Add the Caddy header block documented at the top of this file.`,
  );
  process.exit(WARN_ONLY ? 0 : 1);
}
console.log('\nall required security headers present');
