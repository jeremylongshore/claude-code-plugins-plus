# Network Security

## Network Security

### Firewall Configuration

```
Required endpoints for Cursor:

Cursor services:
- api.cursor.com
- auth.cursor.com
- telemetry.cursor.com (optional)

AI providers:
- api.openai.com
- api.anthropic.com
- api.azure.com (if using Azure)

VS Code/Extensions:
- marketplace.visualstudio.com
- update.code.visualstudio.com
```

### Proxy Configuration

```json
// settings.json
{
  // HTTP proxy
  "http.proxy": "http://proxy.company.com:8080",

  // Proxy authorization
  "http.proxyAuthorization": "Basic base64credentials",

  // Strict SSL
  "http.proxyStrictSSL": true
}
```
