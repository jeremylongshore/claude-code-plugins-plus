---
name: juicebox-deploy-integration
description: |
  Deploy Juicebox integrations.
  Trigger: "deploy juicebox", "juicebox production deploy".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, recruiting, juicebox]
compatible-with: claude-code
---

# Juicebox Deploy Integration

## Docker
```dockerfile
FROM node:20-slim
WORKDIR /app
COPY package*.json ./
RUN npm ci --production
COPY dist/ ./dist/
ENV JUICEBOX_API_KEY=""
CMD ["node", "dist/index.js"]
```

## Cloud Run
```bash
echo -n "jb_live_..." | gcloud secrets create juicebox-key --data-file=-
gcloud run deploy recruiter-svc --set-secrets JUICEBOX_API_KEY=juicebox-key:latest
```

## Resources
- [Juicebox API](https://docs.juicebox.work)

## Next Steps
See `juicebox-webhooks-events`.
