# Server-Fingerprinting Theory

## Why version disclosure is the cheapest pre-attack recon

Every web server, application framework, and runtime has a published
list of CVEs. The CVE catalog is queryable by component name + version.
Disclosing "nginx 1.18.0" hands the attacker an exact filter to apply
against the CVE catalog and produce a list of unauthenticated remote
exploits affecting that version. The exploitation cost goes from "scan
for arbitrary issues" to "execute the specific exploits known to work
against this version."

Most fingerprinting disclosures are not in themselves vulnerabilities —
they're CVSS-low / informational findings. But the cumulative effect
is that the attacker arrives at the application with a pre-prepared
attack toolkit calibrated to the exact software in use. The defensive
posture is "make the attacker work for the recon" — strip the
identifying headers, even though doing so doesn't strictly fix any
specific CVE.

## Header-by-header

### `Server`

The classic. nginx, Apache, and IIS all default to including their
name + version. Most modern reverse proxies have been configured to
strip on outbound by default; legacy stacks still leak.

Worst case: `Server: Apache/2.2.15 (CentOS)` — three pieces of info
in one header. Apache version (2.2 is end-of-life). OS family
(CentOS). And the CentOS minor often differentiable by which Apache
backport-patch level shows up.

Fix is one config directive per server:

- nginx: `server_tokens off;`
- Apache: `ServerTokens Prod`
- Caddy: doesn't disclose since v2.0
- IIS: URL Rewrite module → outbound rule to strip

### `X-Powered-By`

PHP, Express, ASP.NET — frameworks that announce their identity by
default.

- `X-Powered-By: PHP/7.4.21` — exact runtime version. Lookup CVEs
  against PHP 7.4.x — the EOL date for PHP 7.4 was November 2022, so
  anything 7.4-shaped is end-of-life and a target for unpatched-EOL
  exploitation.
- `X-Powered-By: Express` — Node.js Express identification.
- `X-Powered-By: ASP.NET` — .NET stack identification.

Each is a single config line away from elimination.

### `X-AspNet-Version` / `X-AspNetMvc-Version`

.NET runtime exact version. Higher severity than generic
X-Powered-By because the dotnet version pins the runtime + the BCL
version + the ASP.NET version simultaneously. CVE catalog hits multiply.

Disable via `web.config`:

```xml
<httpRuntime enableVersionHeader="false" />
```

### `X-Generator`

CMS family marker. Drupal, Joomla, and WordPress all add a generator
header by default. Drupal includes the major version
(`X-Generator: Drupal 9`); WordPress used to include the full version
in `<meta name="generator">` HTML.

For CMS targets specifically, fingerprint → CVE chain is heavily
weighted toward the CMS itself (Drupal core + module CVEs) and the
themes / plugins layered on top.

### `Via`

HTTP/1.1 standard header for proxy chain identification. Some setups
include the upstream's hostname + version, others use a generic token.

`Via: 1.1 varnish-v4` → reveals Varnish in front of origin.
`Via: 1.1 google` → CloudFront.

Less sensitive than direct server-version disclosure, but informs
network architecture.

### Framework-default cookies

Frameworks set session cookies with predictable names:

| Cookie name | Framework |
|---|---|
| `PHPSESSID` | PHP |
| `JSESSIONID` | Java EE (Tomcat, WebSphere, WebLogic, Spring) |
| `ASP.NET_SessionId` | ASP.NET |
| `ASPSESSIONID*` | Classic ASP |
| `connect.sid` | Express with connect.session |
| `_session_id` | Rails |
| `laravel_session` | Laravel |
| `ci_session` | CodeIgniter |
| `frontend` | Magento |

Any of these in a Set-Cookie response identifies the stack family
even if all version headers are stripped. The remediation is to
rename the session cookie to a non-default value.

It's also a defense in depth: an attacker scanning by JSESSIONID
presence (a common "find me Java apps" scan) misses servers that
renamed the cookie.

### `ETag` format

Apache's default ETag is the file's inode + size + mtime, encoded as
hex. The inode portion is filesystem-specific — across a load-
balanced cluster, two nodes have different inodes for the same file
on different filesystems. Sending requests against the balanced
endpoint and grouping by ETag reveals how many nodes back the
service.

```
"6a7-5b9e..."  <- node A
"3f1-5b9e..."  <- node B
"a2c-5b9e..."  <- node C
```

The size/mtime portion is shared (same file content). The inode is
node-distinguishing.

Apache fix:

```apache
FileETag MTime Size  # drop inode
# Or completely:
FileETag None
```

## Error-page disclosure (CWE-209)

If the application returns a detailed error page on 500-level
responses, the body often includes:

- Server-internal file paths (`/home/app/src/handlers/auth.py`)
- Function names + line numbers (informs source-code structure)
- Framework banner ("Django 4.2", "Spring Boot 3.1", etc.)
- Stack traces with full module paths

Each of these is high-value recon. The fix is per-framework:

| Framework | Disable detailed errors in prod |
|---|---|
| Django | `DEBUG = False` |
| Rails | `config.consider_all_requests_local = false` |
| Spring Boot | `server.error.include-stacktrace=never` |
| ASP.NET | `customErrors mode="RemoteOnly"` |
| Express | `app.use(errorHandler({log:false, debug:false}))` |
| Flask | `app.config['DEBUG'] = False` + `propagate_exceptions=False` |

This is universally a HIGH finding. There's no operational reason
to ship stack traces to production responses.

## The attacker's workflow that this defends against

1. Send one GET to the target homepage.
2. Read `Server`, `X-Powered-By`, `Set-Cookie` from the response.
3. Conclude: nginx 1.18 + PHP 7.4 + Laravel 8.
4. Query CVE catalog: filter to nginx 1.18.x + PHP 7.4.x + Laravel
   8.x. Returns ~15 CVEs.
5. Pick the highest-CVSS unauthenticated-remote one. Execute exploit.

Total elapsed time: about 90 seconds. Defense-in-depth: strip the
headers, rename the cookie, suppress error stack traces. The attacker
now has to do real recon, which raises cost from minutes to hours.

## Primary sources

- [OWASP WSTG-INFO-02 Fingerprint Web Server](https://owasp.org/www-project-web-security-testing-guide/v42/4-Web_Application_Security_Testing/01-Information_Gathering/02-Fingerprint_Web_Server)
- [OWASP WSTG-INFO-08 Fingerprint Web Application Framework](https://owasp.org/www-project-web-security-testing-guide/v42/4-Web_Application_Security_Testing/01-Information_Gathering/08-Fingerprint_Web_Application_Framework)
- [CWE-200 Information Exposure](https://cwe.mitre.org/data/definitions/200.html)
- [CWE-209 Information Exposure Through an Error Message](https://cwe.mitre.org/data/definitions/209.html)
- [nginx server_tokens directive](https://nginx.org/en/docs/http/ngx_http_core_module.html#server_tokens)
- [Apache ServerTokens directive](https://httpd.apache.org/docs/2.4/mod/core.html#servertokens)
