# HTTP Methods — Theory

## TRACE and XST

RFC 7231 §4.3.8 defines TRACE as a debugging method: the server should
echo the request back to the client. The intent was diagnostic — see
exactly what intermediate proxies added or stripped.

The problem: in 2003, Jeremiah Grossman demonstrated Cross-Site Tracing
(XST). An attacker who can execute JavaScript on the origin (e.g., via
XSS) issues an XHR request with method TRACE. The server echoes the
request body — including HttpOnly cookies that XHR-set-cookies cannot
normally read. The attacker's JavaScript reads the response body and
exfiltrates the cookies.

HttpOnly was meant to make session cookies inaccessible to JavaScript;
TRACE makes them accessible again. The fix is to disable TRACE on
every web server, period. There is no legitimate production use case
that requires TRACE.

Modern servers ship with TRACE disabled by default. If you see TRACE
enabled on a target, it's typically a server with hand-rolled config
that forgot to disable it, or a stale install of older nginx/Apache.

## CONNECT

CONNECT (RFC 7231 §4.3.6) is for HTTP proxies: the client asks the
proxy to open a TCP tunnel to a specified destination. Once the tunnel
is established, the proxy blindly forwards bytes both ways.

The danger: if your reverse proxy implements CONNECT, external clients
can ask it to connect to ARBITRARY internal hosts. The proxy obediently
opens TCP to internal-database:5432 and forwards bytes. Cloud metadata
endpoints (169.254.169.254 in AWS / GCP / Azure) are a particular
prize — they require no authentication, exposing credentials and
config to anyone who can reach them.

nginx and Apache reject CONNECT by default. Seeing CONNECT enabled
means someone misconfigured `ProxyRequests On` (Apache) or a
similar nginx pattern.

## DEBUG

Microsoft's IIS shipped a DEBUG HTTP method for ASP.NET application
debugging. Sending `DEBUG /path HTTP/1.0` with `Command: stop-debug`
header would gracefully halt active debugging sessions. The auth model
was implicit — if you could send the request, you could stop debug.

Modern stacks don't use DEBUG. If you see it enabled, the target is
either:

- An older IIS install with debugging features incompletely disabled
- A development server (Flask dev, Django runserver) exposed publicly
- A custom server that recognizes the method by accident

Any of those is worth investigating.

## PUT and DELETE

Both are legitimate REST methods. The "dangerous" part is when they're
exposed on paths the application doesn't actually serve as REST APIs.

The classic exploit: server allows PUT on `/uploads/`. Attacker PUTs a
`.php` (or `.jsp` or `.aspx`) file. Server stores it. Attacker
requests the file; server-side runtime executes it. Full RCE from one
unauthenticated PUT.

Modern frameworks (Express, FastAPI, Spring, Rails) don't enable
PUT/DELETE on routes unless you explicitly bind handlers. The danger
is at the server-software layer: older nginx with WebDAV module
loaded, older Apache with mod_dav, IIS with WebDAV authoring feature.

If the target is an actual REST API (`/api/v1/users/{id}` should
accept PUT/DELETE with auth), use `--is-api` to suppress the
PUT/DELETE finding — at that point, the audit moves to skill #21
(`confirming-pentest-authorization`) and the authentication-validator
plugin.

## WebDAV (PROPFIND, MKCOL, COPY, MOVE)

RFC 4918 defines WebDAV — an extension of HTTP for collaborative
authoring. Methods:

- PROPFIND: list directory contents + properties
- MKCOL: create new directory
- COPY: copy file/dir on server
- MOVE: move file/dir on server
- LOCK/UNLOCK: file locking for collaborative editing

In modern web stacks WebDAV is essentially unused. It survives as a
default in:

- Older nginx with `dav_methods` enabled in vhost
- Apache with mod_dav loaded
- IIS with WebDAV Publishing role

If WebDAV is enabled and any write method (MKCOL, MOVE, COPY) succeeds
without auth, the consequence is identical to enabling PUT — arbitrary
file write becomes a code-execution vector if the target serves
executable file types.

PROPFIND alone is information disclosure (directory listing). Bounded
risk but rarely intentional in 2026.

## OPTIONS and Allow header

OPTIONS is meant to be informational — "what can I do here?" The
response's Allow header lists supported methods. This is fine in
principle.

The problem: many servers respond with a broad Allow header that
includes methods the application doesn't use. Attackers scrape Allow
to enumerate the method surface and pick targets.

The fix isn't to disable OPTIONS (CORS preflight needs it) — it's to
configure the Allow response to list only methods the application
actually supports. Many frameworks compute Allow dynamically from
registered route handlers, which gives you the correct answer for
free.

`Allow: *` is the worst case — server-asserted "anything goes." Even
when paired with proper handler-level checks, the disclosure of
"anything is on the table" is information attackers can use.

## Why this skill's defaults treat non-API paths strictly

The "is-API" assumption is binary in this skill: either the URL is a
REST API endpoint where PUT/DELETE are expected, or it isn't. In real
production stacks there are mixed cases — `/api/v1/users` serves PUT,
`/index.html` doesn't. The right operational pattern is to run this
skill twice per target with `--is-api` toggled, against representative
URLs of each type.

For monolithic apps where everything is on `/`, treat as non-API and
fix any PUT/DELETE exposure by adding `limit_except GET POST { deny
all; }` at the server level.

## Primary sources

- [RFC 7231 — HTTP/1.1 Semantics §4.3](https://datatracker.ietf.org/doc/html/rfc7231#section-4.3)
- [RFC 4918 — WebDAV](https://datatracker.ietf.org/doc/html/rfc4918)
- [OWASP WSTG-CONF-06 — Test HTTP Methods](https://owasp.org/www-project-web-security-testing-guide/v42/4-Web_Application_Security_Testing/02-Configuration_and_Deployment_Management_Testing/06-Test_HTTP_Methods)
- Jeremiah Grossman — Cross-Site Tracing (XST), 2003
- [CWE-441 — Unintended Proxy or Intermediary](https://cwe.mitre.org/data/definitions/441.html)
- [CWE-538 — File and Directory Information Exposure](https://cwe.mitre.org/data/definitions/538.html)
