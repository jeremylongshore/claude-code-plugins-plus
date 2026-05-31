# Server-Fingerprinting Remediation Playbook

## Strip Server header

### nginx

```nginx
http {
    server_tokens off;
}
```

To go further (replace nginx with a custom token, requires
`headers-more-nginx-module`):

```nginx
more_set_headers "Server: ";  # send empty Server header
```

### Apache

```apache
ServerTokens Prod
ServerSignature Off
```

`ServerTokens Prod` makes the Server header read just `Apache` (no
version, no OS). `ServerSignature Off` removes the footer from
generated error pages.

### Caddy

Caddy 2.x doesn't disclose by default. Verify with `caddy adapt
--pretty` and ensure no override.

### IIS

PowerShell to remove via URL Rewrite outbound rule:

```powershell
# Add outbound rule that strips Server header
$site = "Default Web Site"
$rule = @{
    name = "Strip Server Header"
    patternSyntax = "Wildcard"
    match = "*"
    serverVariable = "RESPONSE_SERVER"
    action = "Rewrite"
    value = ""
}
Add-WebConfigurationProperty -PSPath "IIS:\Sites\$site" -Filter "/system.webServer/rewrite/outboundRules" -Name "." -Value $rule
```

### AWS ALB / CloudFront

ALB: Listener → Add header policy → Drop `Server` header on response.

CloudFront: Behaviors → Response Headers Policy → Custom Headers →
add `Server:` (empty) override.

### Cloudflare

Workers script:

```javascript
addEventListener('fetch', event => event.respondWith(handleRequest(event.request)))
async function handleRequest(req) {
    const resp = await fetch(req);
    const newHeaders = new Headers(resp.headers);
    newHeaders.delete('Server');
    newHeaders.delete('X-Powered-By');
    return new Response(resp.body, {
        status: resp.status,
        statusText: resp.statusText,
        headers: newHeaders,
    });
}
```

## Strip X-Powered-By

### PHP

`php.ini`:

```ini
expose_php = Off
```

### Express

```javascript
app.disable('x-powered-by');
// or with helmet:
const helmet = require('helmet');
app.use(helmet.hidePoweredBy());
```

### ASP.NET

`web.config`:

```xml
<system.webServer>
    <httpProtocol>
        <customHeaders>
            <remove name="X-Powered-By" />
            <remove name="X-AspNet-Version" />
            <remove name="X-AspNetMvc-Version" />
        </customHeaders>
    </httpProtocol>
</system.webServer>
```

Plus for X-AspNet-Version:

```xml
<system.web>
    <httpRuntime enableVersionHeader="false" />
</system.web>
```

Plus for X-AspNetMvc-Version, in `Global.asax`:

```csharp
protected void Application_Start()
{
    MvcHandler.DisableMvcResponseHeader = true;
}
```

## Strip X-Runtime (Rails)

`config/application.rb`:

```ruby
config.middleware.delete Rack::Runtime
# Or globally:
config.action_dispatch.runtime_response_header = nil
```

## Strip X-Generator

### Drupal

```php
// settings.php
$config['system.theme']['default']['generator'] = '';

// Or via custom module hook:
function MYMODULE_preprocess_html(&$variables) {
    unset($variables['head_title']['generator']);
}
```

### WordPress

```php
// functions.php
remove_action('wp_head', 'wp_generator');
```

Also remove the `<meta name="generator">` tag with a similar hook
for the HTML body.

## Rename framework-default cookies

### Express

```javascript
app.use(session({
    name: 'sid',          // not 'connect.sid'
    secret: process.env.SESSION_SECRET,
    cookie: { httpOnly: true, secure: true, sameSite: 'lax' },
}));
```

### Spring Boot

```yaml
server:
  servlet:
    session:
      cookie:
        name: sid       # not JSESSIONID
        http-only: true
        secure: true
```

### Rails

```ruby
# config/initializers/session_store.rb
Rails.application.config.session_store :cookie_store, key: '_sid'
```

### Django

```python
# settings.py
SESSION_COOKIE_NAME = 'sid'   # not 'sessionid'
```

### Laravel

```php
// .env
SESSION_COOKIE=sid

// or config/session.php
'cookie' => env('SESSION_COOKIE', 'sid'),
```

### PHP (native)

```ini
; php.ini
session.name = sid           ; not PHPSESSID
```

## Suppress production error stack traces

### Django

```python
# settings/production.py
DEBUG = False
ADMINS = [('Ops', 'ops@example.com')]  # ops gets the trace via email, not the user
```

### Rails

```ruby
# config/environments/production.rb
config.consider_all_requests_local = false
config.action_dispatch.show_exceptions = true
config.action_dispatch.show_detailed_exceptions = false
```

### Spring Boot

```yaml
server:
  error:
    include-stacktrace: never
    include-message: never
    include-exception: false
    include-binding-errors: never
```

### ASP.NET

`web.config`:

```xml
<system.web>
    <customErrors mode="RemoteOnly" defaultRedirect="~/error" />
</system.web>
```

### Express

```javascript
// Default Express error handler shows stack in development;
// override in production:
app.use((err, req, res, next) => {
    if (req.app.get('env') === 'production') {
        res.status(500).send('Internal Server Error');
    } else {
        next(err);
    }
});
```

### Flask

```python
app.config['DEBUG'] = False
app.config['PROPAGATE_EXCEPTIONS'] = False

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500
```

### Go (net/http stdlib)

```go
// Don't use the default panic handler that prints stack
mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
    defer func() {
        if err := recover(); err != nil {
            // Log internally, return generic message
            log.Printf("panic: %v", err)
            http.Error(w, "Internal Server Error", 500)
        }
    }()
    // ... handler logic
})
```

## Fix Apache ETag fingerprint

```apache
# In httpd.conf or vhost
FileETag MTime Size   # drop inode
# Or:
FileETag None         # disable ETags entirely
```

## CI integration

```yaml
- name: Server-fingerprint posture
  run: |
    python3 plugins/security/penetration-tester/skills/fingerprinting-server-software/scripts/fingerprint_server.py \
        "${{ secrets.PROD_URL }}" \
        --authorized \
        --min-severity medium \
        --format json \
        --output fingerprint-report.json
- run: |
    if jq 'any(.severity == "high" or .severity == "medium")' fingerprint-report.json | grep -q true; then
      echo "::warning::Server-fingerprint findings present"
    fi
```

## Verification after remediation

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/fingerprinting-server-software/scripts/fingerprint_server.py \
    https://example.com --authorized --min-severity medium --trigger-error
```

Expected: exit 0, zero MEDIUM-or-higher findings. LOW findings on
framework-default cookies are acceptable trade-offs if you've judged
the recon-cost-vs-rename-pain tradeoff and chose to keep defaults.
