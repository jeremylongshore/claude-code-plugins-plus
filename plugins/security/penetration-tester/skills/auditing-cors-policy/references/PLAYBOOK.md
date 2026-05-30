# CORS Remediation Playbook

## Pattern 1 — Replace reflection with allow-list

### nginx

```nginx
map $http_origin $cors_origin {
    default "";
    "~^https://app\.example\.com$" "$http_origin";
    "~^https://admin\.example\.com$" "$http_origin";
}

server {
    location /api/ {
        add_header Access-Control-Allow-Origin $cors_origin always;
        add_header Access-Control-Allow-Credentials true always;
        add_header Vary Origin always;
        if ($request_method = OPTIONS) {
            add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE" always;
            add_header Access-Control-Allow-Headers "Authorization, Content-Type" always;
            add_header Access-Control-Max-Age 3600 always;
            return 204;
        }
    }
}
```

The `map` directive evaluates each allowed origin pattern. If none match, `$cors_origin` is empty and the Allow-Origin header is sent empty (browser rejects, request blocked).

### Express (Node.js)

```js
const cors = require('cors');
app.use('/api', cors({
    origin: ['https://app.example.com', 'https://admin.example.com'],
    credentials: true,
    methods: ['GET', 'POST', 'PUT', 'DELETE'],
    allowedHeaders: ['Authorization', 'Content-Type'],
    maxAge: 3600,
}));
```

The `cors` middleware sets `Vary: Origin` automatically; the `origin` array does exact-match against the request Origin.

### Spring (Java)

```java
@Configuration
public class WebConfig implements WebMvcConfigurer {
    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/**")
            .allowedOrigins("https://app.example.com", "https://admin.example.com")
            .allowedMethods("GET", "POST", "PUT", "DELETE")
            .allowedHeaders("Authorization", "Content-Type")
            .allowCredentials(true)
            .maxAge(3600);
    }
}
```

### FastAPI (Python)

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.example.com", "https://admin.example.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=3600,
)
```

### Rails 7

```ruby
# config/initializers/cors.rb
Rails.application.config.middleware.insert_before 0, Rack::Cors do
    allow do
        origins 'app.example.com', 'admin.example.com'  # exact list
        resource '/api/*',
            headers: :any,
            methods: [:get, :post, :put, :delete],
            credentials: true,
            max_age: 3600
    end
end
```

## Pattern 2 — Fix subdomain pattern matching

### Wrong (JavaScript)

```js
if (origin.endsWith('.example.com')) { allow(origin); }
```

Matches `evil.example.com.attacker.com`.

### Right (JavaScript)

```js
const url = new URL(origin);
const trustedHosts = ['example.com'];
if (
    trustedHosts.includes(url.hostname) ||
    trustedHosts.some(h => url.hostname.endsWith('.' + h))
) {
    allow(origin);
}
```

The `new URL()` parse + `hostname` extraction + leading-dot check eliminates the suffix-string bypass.

### Right (Python)

```python
from urllib.parse import urlparse

TRUSTED_HOSTS = {'example.com'}

def is_origin_allowed(origin: str) -> bool:
    try:
        hostname = urlparse(origin).hostname
    except Exception:
        return False
    if hostname in TRUSTED_HOSTS:
        return True
    return any(hostname.endswith('.' + h) for h in TRUSTED_HOSTS)
```

## Pattern 3 — Remove Allow-Origin:null trust

If your allow-list contains the string `'null'`, remove it. There's no legitimate cross-origin sender of Origin:null worth trusting.

Edge case: if you have a legitimate use case for sandboxed-iframe access to a specific endpoint, design around it explicitly (e.g., a separate auth-token-in-URL flow); do not extend CORS trust to Origin:null.

## Pattern 4 — Always set Vary:Origin when per-origin

### nginx (global for /api/)

```nginx
location /api/ {
    add_header Vary Origin always;
}
```

### Caddy

```caddy
example.com {
    header /api/* Vary Origin
}
```

### CDN-level (CloudFlare Workers, Fastly VCL)

Inject `Vary: Origin` on every response from your origin behind the CDN. Configure the CDN to respect Vary on cache lookups.

## Pattern 5 — Cap preflight cache at 24h or less

Browsers cap at 7200s anyway, so setting it to 3600 is the practical move:

```
Access-Control-Max-Age: 3600
```

Anything higher confuses the next engineer reading the config.

## Pattern 6 — Restrict Allow-Methods

Replace `Access-Control-Allow-Methods: *` with the explicit list of methods your endpoint actually serves:

```
Access-Control-Allow-Methods: GET, POST, PUT, DELETE
```

## Pattern 7 — Disable Allow-Credentials if not needed

If your endpoint doesn't need to read user cookies cross-origin (most public APIs don't — they use Authorization: Bearer instead), drop `Access-Control-Allow-Credentials: true` entirely. This eliminates the entire credential-theft attack surface.

For bearer-token APIs:

```
Access-Control-Allow-Origin: *
# (no Allow-Credentials — bearer tokens come in Authorization header, not cookies)
```

The wildcard is safe here because the browser won't attach cookies; the only way to authenticate is the bearer token, which the cross-origin JS already had to obtain.

## CI integration

```yaml
- name: CORS audit on changed endpoints
  run: |
    for ENDPOINT in $(./scripts/list-changed-endpoints.sh); do
      python3 plugins/security/penetration-tester/skills/auditing-cors-policy/scripts/audit_cors.py \
          "$ENDPOINT" --authorized --min-severity high --format jsonl >> cors-audit.jsonl
    done
- run: |
    if [ -s cors-audit.jsonl ] && jq -s 'any(.severity == "critical" or .severity == "high")' cors-audit.jsonl | grep -q true; then
      echo "::error::CORS audit found high/critical findings"
      exit 1
    fi
```

## Verification after remediation

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/auditing-cors-policy/scripts/audit_cors.py \
    https://api.example.com/endpoint \
    --authorized \
    --min-severity high
```

Expected: exit code 0, only INFO-level finding "No CORS misconfiguration detected".
