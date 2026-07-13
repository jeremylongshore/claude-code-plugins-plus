# API Documentation Generation Examples

## Redoc Configuration

```yaml
# docs/config/redoc.yaml
openapi: ./openapi.yaml
output: ./docs/site/index.html
options:
  theme:
    colors:
      primary:
        main: '#1a73e8'
    typography:
      fontFamily: 'Inter, sans-serif'
    sidebar:
      backgroundColor: '#1e1e2e'
  hideDownloadButton: false
  expandResponses: '200,201'
  requiredPropsFirst: true
  pathInMiddlePanel: true
```

## Multi-Language Code Example Generator

```javascript
// docs/examples/generate-examples.js
function generateExamples(method, path, headers, body) {
  const url = `https://api.example.com${path}`;
  return {
    curl: generateCurl(method, url, headers, body),
    javascript: generateJS(method, url, headers, body),
    python: generatePython(method, url, headers, body),
  };
}

function generateCurl(method, url, headers, body) {
  let cmd = `curl -X ${method} "${url}"`;
  for (const [k, v] of Object.entries(headers)) {
    cmd += `\n  -H "${k}: ${v}"`;
  }
  if (body) cmd += `\n  -d '${JSON.stringify(body, null, 2)}'`;
  return cmd;
}

function generateJS(method, url, headers, body) {
  return `const response = await fetch("${url}", {
  method: "${method}",
  headers: ${JSON.stringify(headers, null, 4)},${body ? `
  body: JSON.stringify(${JSON.stringify(body, null, 4)}),` : ''}
});
const data = await response.json();`;
}

function generatePython(method, url, headers, body) {
  return `import httpx
response = httpx.${method.toLowerCase()}("${url}",
    headers=${JSON.stringify(headers)},${body ? `
    json=${JSON.stringify(body)},` : ''})
data = response.json()`;
}
```

## Generated Code Example Output

```bash
# curl
curl -X POST "https://api.example.com/users" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice Smith", "email": "alice@example.com"}'
```

```javascript
// JavaScript (fetch)
const response = await fetch("https://api.example.com/users", {
  method: "POST",
  headers: {
    "Authorization": "Bearer YOUR_API_KEY",
    "Content-Type": "application/json"
  },
  body: JSON.stringify({ name: "Alice Smith", email: "alice@example.com" }),
});
const user = await response.json();
// { "id": "usr_abc123", "name": "Alice Smith", ... }
```

```python
# Python (httpx)
import httpx
response = httpx.post("https://api.example.com/users",
    headers={"Authorization": "Bearer YOUR_API_KEY"},
    json={"name": "Alice Smith", "email": "alice@example.com"})
user = response.json()
```

## Authentication Guide Template

```markdown
## API Key Authentication
Include your key in the X-API-Key header:
curl https://api.example.com/users -H "X-API-Key: sk_live_abc123..."

## OAuth 2.0 Bearer Token
1. Obtain a token:
curl -X POST https://auth.example.com/oauth/token \
  -d "grant_type=client_credentials&client_id=ID&client_secret=SECRET"

2. Use the token:
curl https://api.example.com/users -H "Authorization: Bearer eyJhbG..."
```

## Error Reference Table

```markdown
| Status | Code | Description | Resolution |
|--------|------|-------------|------------|
| 400 | VALIDATION_ERROR | Invalid fields | Check errors array |
| 401 | TOKEN_EXPIRED | Token expired | Refresh or re-auth |
| 403 | INSUFFICIENT_SCOPE | Missing scope | Request more scopes |
| 404 | RESOURCE_NOT_FOUND | ID not found | Verify resource ID |
| 429 | RATE_LIMITED | Too many requests | Wait Retry-After seconds |
```

## CI Documentation Deployment

```yaml
# .github/workflows/docs.yml
name: Deploy API Docs
on:
  push:
    paths: ['openapi.yaml']
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npx @redocly/cli lint openapi.yaml
      - run: npx @redocly/cli build-docs openapi.yaml -o docs/site/index.html
      - run: node docs/examples/generate-examples.js
      - uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./docs/site
```

## Versioned Documentation

```javascript
const versions = ['v1', 'v2'];
for (const version of versions) {
  execSync(
    `npx @redocly/cli build-docs specs/openapi-${version}.yaml ` +
    `-o docs/site/${version}/index.html`
  );
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
