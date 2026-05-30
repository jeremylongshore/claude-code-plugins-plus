# HTTP Security Headers — Theory

## HSTS (Strict-Transport-Security)

The first HTTPS visit is the soft spot. A network attacker sees the
client typing `example.com` (HTTP-by-default) and rewrites the response
to keep the conversation in cleartext (sslstrip pattern). HSTS closes
this by pinning HTTPS: once the client has seen the header, it refuses
to downgrade for the duration of `max-age`.

For new clients (cache empty), HSTS doesn't help — the attacker still
gets the first-visit window. The HSTS preload list closes that gap:
sites on the list ship with browsers, so even first-visit users have
HSTS pinned. Requirements for preload submission:

- HTTPS only (no HTTP fallback)
- `max-age` ≥ 31536000s (1 year)
- `includeSubDomains` directive present
- `preload` directive present
- Manual submission at hstspreload.org

Removal from the preload list takes 6–12 months (browsers ship the list
in release binaries). Submit only when committed.

## CSP (Content-Security-Policy)

The browser-enforced rule set for what content the page can load and
execute. The most effective single mitigation against XSS in the modern
web stack — a CSP that blocks `'unsafe-inline'` and uses nonces or
hashes for legitimate inline script means an injected `<script>alert(1)</script>` simply doesn't execute, even if the
injection point exists.

Rollout pattern:

1. Start with `Content-Security-Policy-Report-Only` and a violation
   endpoint (`report-uri /csp-report`).
2. Collect violations for 2-4 weeks; categorize legitimate vs attack.
3. Tighten the policy to permit the legitimate set; switch to
   enforcing (`Content-Security-Policy` instead of report-only).
4. Track violation rate; expect <1 / 10K page views in steady state.

Common pitfalls:

- `'unsafe-inline'` — the lazy default; defeats the XSS protection.
  Replace inline handlers with addEventListener.
- `'unsafe-eval'` — needed only by legacy build outputs; audit and
  upgrade.
- Over-broad `default-src` — `default-src *` defeats every directive
  except those explicitly tighter.
- Forgotten `frame-ancestors` — clickjacking opens if X-Frame-Options
  is also missing.

## X-Frame-Options vs CSP frame-ancestors

X-Frame-Options is the legacy single-purpose header — DENY, SAMEORIGIN,
or ALLOW-FROM. CSP `frame-ancestors` is the modern replacement with
finer granularity. The browser respects both; if both present they
both apply (most restrictive wins).

For new sites, prefer `frame-ancestors`. For sites supporting older
browsers (IE11 stragglers, embedded browsers in legacy mobile OSes),
ship both.

## X-Content-Type-Options: nosniff

Without nosniff, the browser may "MIME-sniff" a response served as
text/plain or application/octet-stream and decide it looks like HTML
or JavaScript and execute it. The attack: upload a file with a .txt
extension containing JavaScript; the server serves it as text/plain;
the browser sniffs, sees `<script>`, executes.

`nosniff` tells the browser to trust the Content-Type header. Combined
with strict Content-Type values on user-uploaded content, this closes
the class.

## Referrer-Policy

`Referer` (sic — the original spec misspelling persists) leaks the
URL the user navigated from. Cross-origin, this is a privacy issue
(internal URLs in your URL paths leak to wherever your users click
links to). Within-origin it's useful for analytics.

Modern recommendation: `strict-origin-when-cross-origin` — sends full
URL same-origin, just the origin cross-origin. Strikes the right
balance for most apps.

`unsafe-url` sends everything to everyone. Don't.

## Permissions-Policy

Successor to Feature-Policy. Declares which device capabilities the
page can request: camera, microphone, geolocation, USB, serial, idle-
detection, etc. Default browser behavior is to PROMPT the user if the
page asks; Permissions-Policy lets you assert "this page never asks"
which is a defense-in-depth against compromised-page scenarios.

Sensible baseline: `Permissions-Policy: camera=(), microphone=(),
geolocation=(), interest-cohort=()`. `interest-cohort=()` opts out of
FLoC / Topics API for users.

## Server header version disclosure

`Server: nginx/1.18.0` lets a scanner immediately enumerate every CVE
affecting that nginx version. Information disclosure (CWE-200). Fix is
trivial:

- nginx: `server_tokens off;` → "nginx" without version
- Apache: `ServerTokens Prod` → "Apache" without version
- Caddy: doesn't disclose by default

This isn't critical — sophisticated attackers fingerprint via response
behavior, not headers. But it's free defense and audit-checkable.

## Cache-Control on authenticated endpoints

The trap: developer sets `Cache-Control: max-age=300` for performance.
The endpoint serves authenticated content. A shared cache (corporate
proxy, CDN edge) stores the response. The next request from a
different user hits the cache and gets the first user's response.

The fix is per-spec: `Cache-Control: private` (only the end-user's
browser may cache) or `Cache-Control: no-store` (no caching anywhere).
For authenticated APIs, `no-store` is the safer default; `private`
allows browser-side caching which can leak in shared-device contexts.

The pattern is so common that auditors call it out under CWE-525
"Information Exposure Through Browser Caching".

## Primary sources

- [OWASP Secure Headers Project](https://owasp.org/www-project-secure-headers/)
- [MDN — Strict-Transport-Security](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Strict-Transport-Security)
- [MDN — Content-Security-Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy)
- [MDN — Permissions-Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Permissions-Policy)
- [hstspreload.org](https://hstspreload.org/)
- [Mozilla Observatory](https://observatory.mozilla.org/)
- [W3C Permissions Policy](https://www.w3.org/TR/permissions-policy/)
