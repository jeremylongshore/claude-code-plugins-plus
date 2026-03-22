---
name: linktree-deploy-integration
description: |
  Deploy Integration for Linktree.
  Trigger: "linktree deploy integration".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, linktree, social]
compatible-with: claude-code
---

# Linktree Deploy Integration

## Docker
```dockerfile
FROM node:20-slim
WORKDIR /app
COPY package*.json ./
RUN npm ci --production
COPY dist/ ./dist/
ENV LINKTREE_API_KEY=""
CMD ["node", "dist/index.js"]
```

## Resources
- [Linktree Docs](https://linktr.ee/marketplace/developer)

## Next Steps
See `linktree-webhooks-events`.
