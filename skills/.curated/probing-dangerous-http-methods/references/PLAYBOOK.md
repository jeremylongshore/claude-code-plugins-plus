# HTTP Methods — Remediation Playbook

## Disable TRACE

### nginx

```nginx
server {
    listen 443 ssl http2;
    server_name example.com;

    if ($request_method = TRACE) {
        return 405;
    }

    # ... rest of config ...
}
```

The `if` directive is generally discouraged in nginx, but this is the
canonical pattern for method filtering and is safe.

### Apache (httpd 2.4)

```apache
TraceEnable Off
```

This is a server-global directive; place it in the main config.

### IIS

1. IIS Manager → site → Request Filtering → HTTP Verbs tab.
2. Click "Deny Verb" → enter `TRACE`.
3. Apply.

### AWS ALB

ALB doesn't expose method-level filtering directly. Use a Lambda@Edge
function or WAF rule:

```json
{
    "Type": "RegexMatchStatement",
    "FieldToMatch": {"Method": {}},
    "RegexString": "^(TRACE|CONNECT|DEBUG|PROPFIND|MKCOL|COPY|MOVE)$",
    "Action": "Block"
}
```

### Cloudflare WAF

```
http.request.method in {"TRACE" "CONNECT" "DEBUG" "PROPFIND" "MKCOL" "COPY" "MOVE"}
```

Action: Block.

## Disable CONNECT

CONNECT should never be enabled on a public-facing server. If your
audit found it enabled, the cause is one of:

### Apache with mod_proxy as forward proxy

Bad:

```apache
ProxyRequests On
```

Fix: change to `ProxyRequests Off`. The reverse-proxy `ProxyPass` and
`ProxyPassReverse` directives still work without it.

### nginx misconfigured as forward proxy

Check for `proxy_method CONNECT` anywhere in config and remove.

### Squid or other proxy software exposed publicly

Move the proxy behind authentication or behind a VPN; don't expose it
publicly.

## Disable DEBUG (IIS)

1. IIS Manager → site → Handler Mappings.
2. Find any handler with DEBUG in its verb list (typically aspnet
   handlers).
3. Edit → remove DEBUG from the Verb field.
4. Restart IIS.

Express dev: ensure `process.env.NODE_ENV === 'production'`. The
Express dev middleware exposes DEBUG only in non-production mode.

## Disable PUT and DELETE on non-API paths

### nginx

```nginx
location / {
    limit_except GET POST HEAD {
        deny all;
    }
}

location /api/ {
    # API location — all methods allowed; auth handled by upstream
    proxy_pass http://api-backend;
}
```

### Apache

```apache
<Location />
    <LimitExcept GET POST HEAD>
        Require all denied
    </LimitExcept>
</Location>

<Location /api>
    # API location
</Location>
```

### Express (Node.js)

By default, Express only handles routes you register. To explicitly
block:

```js
app.all('*', (req, res, next) => {
    const allowed = ['GET', 'POST', 'HEAD', 'OPTIONS'];
    if (!allowed.includes(req.method)) {
        return res.status(405).send('Method Not Allowed');
    }
    next();
});
```

## Disable WebDAV

### nginx

Check vhost for any `dav_methods` directive:

```nginx
location / {
    dav_methods off;  # explicit
}
```

The default is `off`, but some sample configs enable it implicitly.

If your nginx was compiled with `--with-http_dav_module`, recompile
without it or move to a packaged binary that doesn't include it.

### Apache

```apache
# Comment out or remove:
# LoadModule dav_module modules/mod_dav.so
# LoadModule dav_fs_module modules/mod_dav_fs.so

# If you can't remove the module, deny WebDAV methods explicitly:
<Location />
    <LimitExcept GET POST HEAD OPTIONS>
        Require all denied
    </LimitExcept>
</Location>
```

### IIS

Server Manager → Roles & Features → uncheck "WebDAV Publishing" under
Web Server (IIS) → Common HTTP Features. Restart IIS.

Or via PowerShell:

```powershell
Uninstall-WindowsFeature -Name Web-DAV-Publishing
```

## Restrict OPTIONS Allow header

The right approach is to let the framework compute Allow from
registered routes; most modern frameworks do this by default.

### nginx custom Allow response

If you need to override:

```nginx
location /api/users {
    if ($request_method = OPTIONS) {
        add_header Allow "GET, POST, PUT, DELETE, OPTIONS";
        return 204;
    }
}
```

## CI integration

```yaml
- name: HTTP method probe
  run: |
    python3 plugins/security/penetration-tester/skills/probing-dangerous-http-methods/scripts/probe_methods.py \
        "${{ secrets.PROD_URL }}" \
        --authorized \
        --min-severity high \
        --format json \
        --output method-probe.json
- run: |
    if jq 'any(.severity == "critical" or .severity == "high")' method-probe.json | grep -q true; then
      echo "::error::Dangerous HTTP method found enabled"
      exit 1
    fi
```

Recommended cadence: every deploy + nightly. WAF/LB config drift is
the most common regression source.

## Verification after remediation

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/probing-dangerous-http-methods/scripts/probe_methods.py \
    https://example.com \
    --authorized \
    --min-severity medium
```

Expected: exit 0, no MEDIUM-or-higher findings. INFO findings about
"OPTIONS Allow discloses unused methods" may persist if your framework's
default Allow is broad; consider customizing per the section above.
