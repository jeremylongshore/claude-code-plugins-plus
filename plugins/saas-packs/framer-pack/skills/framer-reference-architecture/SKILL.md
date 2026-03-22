---
name: framer-reference-architecture
description: |
  Implement Framer reference architecture with best-practice project layout.
  Use when designing new Framer integrations, reviewing project structure,
  or establishing architecture standards for Framer applications.
  Trigger with phrases like "framer architecture", "framer best practices",
  "framer project structure", "how to organize framer", "framer layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, framer]
compatible-with: claude-code
---

# Framer Reference Architecture

## Overview

Production architecture for Framer integrations covering plugins, Server API CMS sync, code components, and automated publishing pipelines.

## Architecture Diagram

```
┌─────────────────────────────────────────────┐
│               Framer Editor                  │
│  ┌──────────┐  ┌───────────┐  ┌──────────┐ │
│  │ Plugins  │  │ Code      │  │ Code     │ │
│  │ (iframe) │  │ Components│  │ Overrides│ │
│  └────┬─────┘  └───────────┘  └──────────┘ │
│       │ framer-plugin SDK                    │
├───────┴──────────────────────────────────────┤
│             Framer CMS                       │
│  ┌──────────────┐  ┌───────────────────┐    │
│  │ Managed      │  │ Unmanaged         │    │
│  │ Collections  │  │ Collections       │    │
│  └──────┬───────┘  └───────────────────┘    │
├─────────┴────────────────────────────────────┤
│         Server API (WebSocket)               │
│  framer-api package                          │
└─────────┬────────────────────────────────────┘
          │
┌─────────┴────────────────────────────────────┐
│         Your Backend                          │
│  ┌────────────┐  ┌──────────┐  ┌──────────┐ │
│  │ CMS Sync   │  │ Webhook  │  │ CI/CD    │ │
│  │ Service    │  │ Handler  │  │ Pipeline │ │
│  └────────────┘  └──────────┘  └──────────┘ │
└──────────────────────────────────────────────┘
```

## Project Structure

```
framer-integration/
├── plugin/                    # Framer editor plugin
│   ├── src/
│   │   ├── App.tsx           # Plugin UI
│   │   ├── hooks/            # Plugin state hooks
│   │   └── cms/              # CMS sync logic
│   ├── vite.config.ts
│   └── package.json
├── server/                    # Server API backend
│   ├── src/
│   │   ├── sync.ts           # CMS sync service
│   │   ├── publish.ts        # Auto-publish logic
│   │   └── webhooks.ts       # External webhook handlers
│   └── package.json
├── components/                # Shared code components
│   ├── AnimatedCounter.tsx
│   ├── DataList.tsx
│   └── index.ts
├── overrides/                 # Shared code overrides
│   ├── animations.tsx
│   └── interactions.tsx
└── .env.example
```

## Integration Patterns

| Pattern | When | How |
|---------|------|-----|
| Plugin CMS Sync | User-initiated sync | Plugin UI → managed collection |
| Server API Sync | Automated/scheduled | Node.js → Server API WebSocket |
| CI/CD Publish | On content change | GitHub Actions → Server API → publish |
| Webhook Bridge | External CMS events | Webhook → your API → Server API |

## Decision Matrix

| Need | Solution |
|------|----------|
| Custom UI in editor | Framer Plugin |
| Headless CMS sync | Server API |
| Custom interactive elements | Code Components |
| Modify existing animations | Code Overrides |
| Automated publishing | Server API + CI/CD |

## Resources

- [Framer Developers](https://www.framer.com/developers/)
- [Server API](https://www.framer.com/developers/server-api-introduction)
- [CMS API](https://www.framer.com/developers/cms)
- [Plugin Introduction](https://www.framer.com/developers/plugins-introduction)

## Next Steps

Start with `framer-install-auth` to set up your development environment.
