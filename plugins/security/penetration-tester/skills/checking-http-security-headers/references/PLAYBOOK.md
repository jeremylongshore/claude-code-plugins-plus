# HTTP Security Headers — Remediation Playbook

## Baseline security-header bundle (every site)

### nginx

```nginx
server {
    listen 443 ssl http2;
    server_name example.com;

    # HSTS — preload-eligible
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

    # Clickjacking
    add_header X-Frame-Options "DENY" always;

    # MIME sniffing
    add_header X-Content-Type-Options "nosniff" always;

    # Referrer
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Permissions baseline
    add_header Permissions-Policy "camera=(), microphone=(), geolocation=(), interest-cohort=()" always;

    # CSP — start with report-only, tighten after collection
    add_header Content-Security-Policy-Report-Only "default-src 'self'; report-uri /csp-report" always;

    # Hide nginx version
    server_tokens off;

    # ... your location blocks ...
}
```

The `always` flag is critical — without it nginx skips the headers on
non-2xx responses, leaving error pages unprotected.

### Caddy

```caddy
example.com {
    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
        X-Frame-Options "DENY"
        X-Content-Type-Options "nosniff"
        Referrer-Policy "strict-origin-when-cross-origin"
        Permissions-Policy "camera=(), microphone=(), geolocation=(), interest-cohort=()"
        Content-Security-Policy-Report-Only "default-src 'self'; report-uri /csp-report"
        -Server
    }
}
```

### Apache (.htaccess or vhost)

```apache
<IfModule mod_headers.c>
    Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
    Header always set X-Frame-Options "DENY"
    Header always set X-Content-Type-Options "nosniff"
    Header always set Referrer-Policy "strict-origin-when-cross-origin"
    Header always set Permissions-Policy "camera=(), microphone=(), geolocation=(), interest-cohort=()"
    Header always set Content-Security-Policy-Report-Only "default-src 'self'; report-uri /csp-report"
</IfModule>

ServerTokens Prod
ServerSignature Off
```

### Express (Node.js) via helmet

```js
const helmet = require('helmet');
app.use(helmet({
    contentSecurityPolicy: {
        directives: {
            defaultSrc: ["'self'"],
            scriptSrc: ["'self'"],  // no unsafe-inline
            styleSrc: ["'self'"],
        },
        reportOnly: true,
    },
    hsts: { maxAge: 31536000, includeSubDomains: true, preload: true },
    referrerPolicy: { policy: 'strict-origin-when-cross-origin' },
}));
app.use((req, res, next) => {
    res.setHeader('Permissions-Policy', 'camera=(), microphone=(), geolocation=(), interest-cohort=()');
    next();
});
```

### FastAPI (Python)

```python
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), interest-cohort=()"
        return response

app.add_middleware(SecurityHeadersMiddleware)
```

### Rails

```ruby
# config/application.rb
config.action_dispatch.default_headers.merge!(
    'Strict-Transport-Security' => 'max-age=31536000; includeSubDomains; preload',
    'X-Frame-Options' => 'DENY',
    'X-Content-Type-Options' => 'nosniff',
    'Referrer-Policy' => 'strict-origin-when-cross-origin',
    'Permissions-Policy' => 'camera=(), microphone=(), geolocation=(), interest-cohort=()',
)

# config/initializers/content_security_policy.rb
Rails.application.config.content_security_policy do |policy|
    policy.default_src :self
    policy.script_src  :self
    policy.style_src   :self
    policy.report_uri '/csp-report'
end
Rails.application.config.content_security_policy_report_only = true
```

## CSP rollout — report-only to enforce

### Step 1 — report-only with violation endpoint

Use the snippets above to ship `Content-Security-Policy-Report-Only`
with a `report-uri`. Set up the endpoint to log violations:

```python
# FastAPI example
@app.post("/csp-report")
async def csp_report(request: Request):
    body = await request.json()
    logger.info("CSP violation", extra={"report": body})
    return Response(status_code=204)
```

### Step 2 — collect for 2-4 weeks

Group violations by `blocked-uri` and `violated-directive`. Categorize:

- Legitimate inline scripts your own code includes → migrate to
  external files or nonce-source.
- Third-party widgets (analytics, chat, fonts) → add to allow-list.
- Genuine injection attempts → keep blocked.

### Step 3 — tighten policy and switch to enforcing

```nginx
add_header Content-Security-Policy "default-src 'self'; script-src 'self' https://cdn.example.com; style-src 'self' 'sha256-...'; report-uri /csp-report" always;
```

### Step 4 — monitor for regressions

Keep the report-uri. Any new violation should trigger a follow-up.

## HSTS preload submission checklist

Before submitting at hstspreload.org:

- [ ] HTTPS-only (HTTP → 301 redirect to HTTPS, not 302)
- [ ] HSTS header on every HTTPS response
- [ ] `max-age` ≥ 31536000
- [ ] `includeSubDomains` directive present
- [ ] `preload` directive present
- [ ] All subdomains serve HTTPS (no http://subdomain.example.com)
- [ ] No mixed content on any page

Submit at https://hstspreload.org/. Approval takes 6-12 weeks; rejection
is typically immediate.

## CI integration

```yaml
- name: Security headers audit
  run: |
    python3 plugins/security/penetration-tester/skills/checking-http-security-headers/scripts/check_headers.py \
        "${{ secrets.PROD_URL }}" \
        --authorized \
        --min-severity high \
        --format json \
        --output headers-audit.json
- run: |
    if jq 'any(.severity == "high" or .severity == "critical")' headers-audit.json | grep -q true; then
      echo "::error::Security headers audit failed"
      exit 1
    fi
```

## Verification after remediation

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/checking-http-security-headers/scripts/check_headers.py \
    https://example.com \
    --authorized \
    --min-severity medium
```

Expected: exit 0, no MEDIUM-or-higher findings. Cross-check with Mozilla
Observatory (https://observatory.mozilla.org/) — target grade A+.
