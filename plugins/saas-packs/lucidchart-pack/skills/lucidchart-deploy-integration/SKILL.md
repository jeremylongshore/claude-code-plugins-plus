---
name: lucidchart-deploy-integration
description: |
  Deploy Integration for Lucidchart.
  Trigger: "lucidchart deploy integration".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, lucidchart, diagramming]
compatible-with: claude-code
---

# Lucidchart Deploy Integration

## Docker
```dockerfile
FROM node:20-slim
WORKDIR /app
COPY package*.json ./
RUN npm ci --production
COPY dist/ ./dist/
ENV LUCID_API_KEY=""
CMD ["node", "dist/index.js"]
```

## Resources
- [Lucidchart Docs](https://developer.lucid.co/reference/overview)

## Next Steps
See `lucidchart-webhooks-events`.
