Fly.io deployment configuration for Shopify apps, including fly.toml and secrets management.

```toml
# fly.toml
app = "my-shopify-app"
primary_region = "iad"

[env]
  NODE_ENV = "production"
  SHOPIFY_API_VERSION = "2025-04"  # Update quarterly — see shopify.dev/docs/api/usage/versioning

[http_service]
  internal_port = 3000
  force_https = true
  auto_stop_machines = "stop"
  auto_start_machines = true
  min_machines_running = 1

[checks]
  [checks.health]
    port = 3000
    type = "http"
    interval = "15s"
    timeout = "2s"
    path = "/health"
```

```bash
# Set secrets (never in fly.toml)
fly secrets set \
  SHOPIFY_API_KEY="your_key" \
  SHOPIFY_API_SECRET="your_secret" \
  SHOPIFY_ACCESS_TOKEN="shpat_xxx"

# Deploy
fly deploy

# Check health
fly status
curl https://my-shopify-app.fly.dev/health
```
