---
name: figma-architecture-variants
description: 'Choose between Figma integration architectures: CLI script, webhook
  service, or plugin.

  Use when deciding how to integrate with Figma, comparing REST API vs Plugin API,

  or planning a Figma-connected application.

  Trigger with phrases like "figma architecture", "figma blueprint",

  "how to integrate figma", "figma plugin vs api", "figma project type".

  '
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- figma
compatibility: Designed for Claude Code
---
# Figma Architecture Variants

## Overview

Three proven architecture patterns for Figma integrations, based on the two primary Figma APIs: the REST API (external tools) and the Plugin API (in-editor experiences).

## Prerequisites

- Clear use case requirements
- Understanding of Figma REST API vs Plugin API differences

## Instructions

### Step 1: Choose Your Architecture

| Architecture | API Used | Best For | Hosting |
|-------------|----------|----------|---------|
| CLI/Script | REST API | Design token sync, asset export | None (runs locally or in CI) |
| Webhook Service | REST API | Real-time automation, Slack bots | Server/serverless |
| Figma Plugin | Plugin API | In-editor tools, design linting | Runs in Figma desktop app |

### Variant A: CLI Script (Simplest)

**Use case:** Extract design tokens, export icons, sync to code

```
Developer runs script
        │
        ▼
  ┌─────────────┐
  │ CLI Script   │  (Node.js)
  │ - extract.ts │
  └──────┬───────┘
         │ GET /v1/files/:key
         │ GET /v1/images/:key
         ▼
  ┌─────────────┐
  │ Figma REST  │
  │ API         │
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │ Output      │
  │ - tokens.css│
  │ - icons/    │
  └─────────────┘
```

```json
{
  "scripts": {
    "figma:tokens": "tsx scripts/extract-tokens.ts",
    "figma:icons": "tsx scripts/export-icons.ts",
    "figma:sync": "npm run figma:tokens && npm run figma:icons"
  }
}
```

**Pros:** Zero infrastructure, runs in CI, easy to debug
**Cons:** Not real-time, manual trigger, no webhook support

---

### Variant B: Webhook Service (Event-Driven)

**Use case:** Auto-sync on file save, Slack notifications, build triggers

```
  ┌─────────────┐
  │ Figma Cloud  │
  │ FILE_UPDATE  │──── Webhook V2 ────┐
  │ FILE_COMMENT │                    │
  └──────────────┘                    │
                                      ▼
                               ┌──────────────┐
                               │ Your Service  │
                               │ (Vercel/Fly)  │
                               ├──────────────┤
                               │ /webhooks     │ ← Verify passcode
                               │ /health       │
                               │ /api/tokens   │
                               └──────┬───────┘
                                      │
                          ┌───────────┼───────────┐
                          ▼           ▼           ▼
                    ┌──────────┐ ┌──────────┐ ┌──────────┐
                    │ Token    │ │ Slack    │ │ CI       │
                    │ Rebuild  │ │ Notify   │ │ Trigger  │
                    └──────────┘ └──────────┘ └──────────┘
```

```typescript
// Minimal webhook service (Express)
const app = express();
app.post('/webhooks/figma', express.json(), verifyPasscode, (req, res) => {
  res.status(200).json({ received: true });
  processEvent(req.body); // async
});
app.get('/health', healthCheck);
app.listen(process.env.PORT || 3000);
```

**Pros:** Real-time, event-driven, no polling waste
**Cons:** Requires hosting, HTTPS endpoint, webhook management

---

### Variant C: Figma Plugin (In-Editor)

**Use case:** Design linting, component generation, data population

```
  ┌─────────────────────────────────────────┐
  │             Figma Desktop App            │
  │                                         │
  │  ┌─────────────┐   ┌─────────────────┐ │
  │  │ Plugin       │   │ Canvas          │ │
  │  │ Sandbox     │   │ (your design)   │ │
  │  │             │   │                 │ │
  │  │ code.ts     │◄──│ figma.currentPage│ │
  │  │ figma.*     │──►│ figma.createRect │ │
  │  │             │   │                 │ │
  │  ├─────────────┤   └─────────────────┘ │
  │  │ UI iframe   │                        │
  │  │ ui.html     │                        │
  │  │ (React/HTML)│                        │
  │  └─────────────┘                        │
  └─────────────────────────────────────────┘
```

```json
// manifest.json
{
  "name": "My Design Linter",
  "id": "1234567890",
  "api": "1.0.0",
  "main": "dist/code.js",
  "ui": "dist/ui.html",
  "editorType": ["figma"],
  "permissions": ["currentuser"]
}
```

```typescript
// code.ts -- Plugin API (runs in Figma sandbox)
// Access the document directly -- no REST API needed
const page = figma.currentPage;
const frames = page.findAll(n => n.type === 'FRAME');

// Create nodes programmatically
const rect = figma.createRectangle();
rect.resize(200, 100);
rect.fills = [{ type: 'SOLID', color: { r: 1, g: 0.5, b: 0 } }];
page.appendChild(rect);

// Read component properties
const components = page.findAll(n => n.type === 'COMPONENT') as ComponentNode[];
for (const comp of components) {
  console.log(`${comp.name}: ${comp.width}x${comp.height}`);
}
```

**Pros:** Direct document access, instant feedback, rich UI
**Cons:** Only works in Figma desktop, no server-side processing, sandboxed

### Step 2: Decision Matrix

| Factor | CLI Script | Webhook Service | Figma Plugin |
|--------|-----------|-----------------|--------------|
| Real-time | No | Yes | Yes (in-editor) |
| Infrastructure | None | Server/serverless | None |
| CI/CD integration | Natural | Via webhook | Not applicable |
| User interaction | No | No | Yes |
| API used | REST API | REST API | Plugin API |
| File modification | No (read-only) | No (read-only) | Yes (full access) |
| Figma app required | No | No | Yes |
| Auth | PAT | PAT + webhook passcode | None (runs in Figma) |

### Step 3: Hybrid Architecture

Many production systems combine variants:

```
CLI (CI) ← Scheduled token sync (daily at 9 AM)
     +
Webhook Service ← Real-time notifications (Slack, rebuild triggers)
     +
Figma Plugin ← In-editor design linting and data population
```

## Output

- Architecture variant selected based on use case
- Data flow documented
- API choice justified (REST vs Plugin)
- Implementation skeleton provided

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| CLI too slow | Full file fetch | Use `depth=1` and `/nodes` |
| Webhook not firing | No HTTPS | Deploy to platform with TLS |
| Plugin sandbox limits | Heavy computation | Offload to REST API via fetch in UI iframe |
| Wrong variant choice | Over-engineering | Start with CLI, add webhook when needed |

## Resources

- [Figma REST API](https://developers.figma.com/docs/rest-api/)
- [Figma Plugin API](https://developers.figma.com/docs/plugins/)
- [Figma Widgets API](https://developers.figma.com/docs/widgets/)
- [Compare Figma APIs](https://www.figma.com/developers/compare-apis)

## Next Steps

For common anti-patterns, see `figma-known-pitfalls`.
