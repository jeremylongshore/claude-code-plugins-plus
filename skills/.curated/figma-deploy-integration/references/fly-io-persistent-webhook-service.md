# Step 3: Fly.io (Persistent Webhook Service)

Deep-dive reference for the `figma-deploy-integration` skill — extracted from the 'Step 3: Fly.io (Persistent Webhook Service)' step of the workflow.

```toml
# fly.toml
app = "figma-webhook-service"
primary_region = "iad"

[env]
  NODE_ENV = "production"

[http_service]
  internal_port = 3000
  force_https = true
  auto_stop_machines = "suspend"
  auto_start_machines = true
  min_machines_running = 1

[[http_service.checks]]
  grace_period = "10s"
  interval = "30s"
  method = "GET"
  path = "/health"
  timeout = "5s"
```

```bash
fly secrets set FIGMA_PAT=figd_your-token
fly secrets set FIGMA_WEBHOOK_PASSCODE=your-passcode
fly deploy
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
