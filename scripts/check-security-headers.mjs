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
 * NOT WIRED AS A BLOCKING CI GATE YET, deliberately: the headers are set in
 * Caddy on the VPS, which is outside this repo. Promote this to a post-deploy
 * gate once that config ships, otherwise it fails for a reason no one in this
 * repo can fix — and a gate nobody can fix is a gate that gets disabled.
 *
 * USAGE
 *   node scripts/check-security-headers.mjs
 *   node scripts/check-security-headers.mjs --url https://staging.example.com
 *   node scripts/check-security-headers.mjs --warn-only   # report, exit 0
 *
 * CADDY CONFIG THIS EXPECTS (apply on the VPS, then `caddy validate` and
 * `systemctl reload caddy` — never restart, it serves live traffic):
 *
 *   header {
 *     X-Frame-Options            "SAMEORIGIN"
 *     X-Content-Type-Options     "nosniff"
 *     Referrer-Policy            "strict-origin-when-cross-origin"
 *     Strict-Transport-Security  "max-age=31536000; includeSubDomains"
 *     Permissions-Policy         "geolocation=(), microphone=(), camera=()"
 *   }
 */

const args = process.argv.slice(2);
const urlArg = args.indexOf('--url');
const URL_ = urlArg !== -1 ? args[urlArg + 1] : 'https://tonsofskills.com/';
const WARN_ONLY = args.includes('--warn-only');

// `required: false` entries are reported but never fail the run — HSTS and
// Permissions-Policy are good practice rather than a fix for an observed hole,
// and starting strict on them would block the change that closes the real gap.
const EXPECT = [
  { name: 'x-frame-options', match: /^(sameorigin|deny)$/i, required: true },
  { name: 'x-content-type-options', match: /^nosniff$/i, required: true },
  { name: 'referrer-policy', match: /.+/, required: true },
  { name: 'strict-transport-security', match: /max-age=\d+/i, required: false },
  { name: 'permissions-policy', match: /.+/, required: false },
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
  const ok = v != null && h.match.test(v);
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
