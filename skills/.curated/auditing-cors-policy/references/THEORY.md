# CORS Theory

## What CORS actually does

By default, a browser running JavaScript on `https://app.example.com`
cannot read responses from `https://api.different.com` — the Same-
Origin Policy blocks the read. CORS is the controlled relaxation: the
target server says "yes, this specific origin can read my responses,
and here are the conditions."

The browser enforces; the server announces. Two header categories:

- **Response headers** (server → browser): `Access-Control-Allow-
  Origin`, `-Credentials`, `-Methods`, `-Headers`, `-Max-Age`, `-Expose-
  Headers`.
- **Request headers** (browser → server): `Origin` (auto-set),
  `Access-Control-Request-Method`, `-Request-Headers` (preflight only).

The browser sends `Origin` on every cross-origin request. If the
response doesn't allow that origin, the browser hides the response
from JavaScript (but the request still hit the server — caveat
explains the CSRF angle below).

For "non-simple" requests (anything other than GET/HEAD/POST with
limited content types, or with custom headers), browsers send an
`OPTIONS` preflight first. The server's preflight response declares
allowed methods + headers + cache duration. If preflight passes, the
real request proceeds.

## Why reflection is dangerous

The "easy" fix when a CORS bug ticket lands: read the incoming Origin
header and echo it into Allow-Origin. The request from
`https://api.partner.com` works; the request from
`https://my-frontend.com` works; QA closes the ticket.

The problem: requests from `https://attacker.example.com` ALSO work.
If the endpoint serves authenticated content and `Allow-Credentials:
true` is set, the browser sends the user's cookies on the cross-origin
request AND lets the attacker's JavaScript read the response. Full
session-theft via a malicious page the victim visits while logged in.

The fix is not "validate the Origin format" — it's "allow-list a
specific set of trusted origins server-side, check exact equality
against that allow-list, return the matched origin or refuse."

## The credentials + wildcard combination

The Fetch standard makes this combo illegal — browsers reject the
response. Server is asserting Allow-Origin:* AND Allow-Credentials:
true; browser sees both, refuses to expose the response to JavaScript.

So why is this a CRITICAL finding? Because the server-side intent is
wrong. A future server-config change could replace * with reflection,
or a future browser bug could relax the rule. The combination signals
the developer didn't understand the model — and that misunderstanding
will recur in the next CORS-related change.

## Subdomain-pattern bypass

A common shorthand: "trust any subdomain of example.com." The naive
implementation in JavaScript / config:

```js
if (origin.endsWith('.example.com')) { allow(origin); }
```

This matches `evil.example.com.attacker.com` because `.endsWith()` on
a string just checks the suffix — it doesn't parse the URL into host
parts. The attacker registers `attacker.com`, sets up DNS for
`*.example.com.attacker.com`, and gets a wildcard CORS pass.

The fix: parse the Origin as a URL, extract `hostname`, then check
either exact equality or proper subdomain logic
(`hostname === 'example.com' || hostname.endsWith('.example.com')`
— note the second form checks the leading dot, which the buggy form
omits).

## Origin: null

Three places this comes from:

1. Sandboxed iframes — `<iframe sandbox>` sends Origin:null.
2. `data:` URLs — pages loaded from data URLs send Origin:null.
3. `file:` URLs — local file pages send Origin:null.

If your server trusts Origin:null, any page that ends up in a
sandboxed iframe can read your cross-origin responses. Attackers
embed your target site in a sandboxed iframe on attacker.com, the
browser sends Origin:null, your server returns Allow-Origin:null,
attacker reads the response.

Never trust Origin:null. There is no legitimate cross-origin use case
that needs it.

## Vary:Origin and CDN cache poisoning

If your CORS response is per-origin (Allow-Origin varies based on the
Origin header), the cache layer must vary on Origin too. Otherwise:

1. User from `https://trusted.com` requests `/api/profile`. Server
   responds `Allow-Origin: https://trusted.com`. CDN caches the response.
2. Attacker from `https://attacker.com` requests `/api/profile`. CDN
   returns the cached response, including `Allow-Origin: https://trusted.com`.
3. Attacker's request still doesn't satisfy the Allow-Origin match
   (browser checks), so no read happens — BUT the cache is now
   serving a different origin's CORS headers to attacker, which
   becomes a poisoning vector for downstream attacks.

The fix: `Vary: Origin` on every CORS-varying response. Every modern
framework's CORS middleware does this; hand-rolled CORS configs
forget it.

## Preflight cache duration

`Access-Control-Max-Age` controls how long the browser caches the
preflight response. Higher = fewer round trips (perf gain) but
slower CORS-policy revocation (if you change the allow-list, browsers
won't re-preflight until cache expires).

Chrome and Firefox cap at 7200s (2h) regardless of what the server
says, so values above 7200s don't actually help. Setting it explicitly
to 86400s (24h) or higher is a misunderstanding rather than a security
issue — flagged LOW for awareness.

## CORS does NOT prevent CSRF

This trips up developers. CORS controls JavaScript's ability to READ
responses cross-origin. The cross-origin REQUEST is still sent
(cookies, headers, everything). If your server changes state based on
the request alone (POST that updates a record without reading the
response), CORS doesn't help.

Pair CORS audit with CSRF audit (skill #13 in another plugin —
`csrf-protection-validator`) for full coverage.

## Primary sources

- [Fetch Standard — CORS protocol](https://fetch.spec.whatwg.org/#cors-protocol)
- [MDN — Cross-Origin Resource Sharing](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
- [OWASP A05:2021 Security Misconfiguration](https://owasp.org/Top10/A05_2021-Security_Misconfiguration/)
- [CWE-942 Permissive Cross-domain Policy with Untrusted Domains](https://cwe.mitre.org/data/definitions/942.html)
