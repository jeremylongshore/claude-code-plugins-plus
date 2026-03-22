---
name: appfolio-deploy-integration
description: |
  Deploy AppFolio integration service to cloud infrastructure.
  Trigger: "deploy appfolio".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, property-management, appfolio, real-estate]
compatible-with: claude-code
---

# appfolio deploy integration | sed 's/\b\(.\)/\u\1/g'

## Cloud Run Deployment
```bash
gcloud run deploy appfolio-integration \
  --source . \
  --region us-central1 \
  --set-secrets=APPFOLIO_CLIENT_ID=appfolio-client-id:latest,APPFOLIO_CLIENT_SECRET=appfolio-client-secret:latest \
  --set-env-vars=APPFOLIO_BASE_URL=https://your-company.appfolio.com/api/v1 \
  --no-allow-unauthenticated
```

## Health Check
```typescript
app.get("/health", async (req, res) => {
  try {
    await client.http.get("/properties");
    res.json({ status: "healthy" });
  } catch { res.status(503).json({ status: "unhealthy" }); }
});
```

## Resources

- [AppFolio Stack APIs](https://www.appfolio.com/stack/partners/api)
- [AppFolio Engineering Blog](https://engineering.appfolio.com)
