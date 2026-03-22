---
name: onenote-deploy-integration
description: |
  Deploy Integration for OneNote.
  Trigger: "onenote deploy integration".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, onenote, microsoft]
compatible-with: claude-code
---

# OneNote Deploy Integration

## Docker
```dockerfile
FROM node:20-slim
WORKDIR /app
COPY package*.json ./
RUN npm ci --production
COPY dist/ ./dist/
ENV MICROSOFT_GRAPH_TOKEN=""
CMD ["node", "dist/index.js"]
```

## Resources
- [OneNote Docs](https://learn.microsoft.com/en-us/graph/api/resources/onenote-api-overview)

## Next Steps
See `onenote-webhooks-events`.
