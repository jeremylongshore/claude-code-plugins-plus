---
name: replit-architecture-variants
description: |
  Choose and implement Replit architecture blueprints: single-file script, modular app, and multi-service.
  Use when designing new Replit apps, choosing the right architecture scale,
  or planning migration paths as your app grows.
  Trigger with phrases like "replit architecture options", "replit blueprint",
  "how to structure replit app", "replit monolith vs service", "replit app scale".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, replit, architecture, scaling]

---
# Replit Architecture Variants

## Overview
Application architectures on Replit at three scales: single-file prototype, modular production app, and multi-service architecture. Each matches Replit's container model, built-in services, and deployment types.

## Prerequisites
- Replit account
- Understanding of deployment types (Static, Autoscale, Reserved VM)
- Familiarity with Replit's storage options

## Architecture Decision Matrix

| Factor | Single-File | Modular App | Multi-Service |
|--------|------------|-------------|---------------|
| **Users** | Prototype, < 100/day | 100-10K/day | 10K+/day |
| **Database** | Replit KV (50 MiB) | PostgreSQL | PostgreSQL + cache |
| **Storage** | Local + KV | Object Storage | Object Storage + CDN |
| **Persistence** | Ephemeral OK | Durable required | Durable required |
| **Deployment** | Repl Run / Autoscale | Autoscale / Reserved VM | Multiple Reserved VMs |
| **Cost** | Free-$7/mo | $7-25/mo | $25+/mo |
| **Always-on** | No (free), Yes (deploy) | Yes (deployment) | Yes (deployment) |

## Instructions

### Variant A: Single-File Script (Prototype)
**Best for:** Bots, scripts, learning, hackathon projects.

```python
# main.py — everything in one file
from flask import Flask, request, jsonify
from replit import db
import os

app = Flask(__name__)

# KV Database for simple state
@app.route('/')
def home():
    count = db.get("visits") or 0
    db["visits"] = count + 1
    return f"Visit #{count + 1}"

@app.route('/api/notes', methods=['GET', 'POST'])
def notes():
    if request.method == 'POST':
        note = request.json
        notes = db.get("notes") or []
        notes.append(note)
        db["notes"] = notes
        return jsonify(note), 201
    return jsonify(db.get("notes") or [])

app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 3000)))
```

```toml
# .replit
run = "python main.py"

[nix]
channel = "stable-24_05"

[deployment]
run = ["python", "main.py"]
deploymentTarget = "autoscale"
```

**Limitations:** 50 MiB data, files lost on restart, cold starts. Upgrade to Variant B when you need structured data or durability.

---

### Variant B: Modular App with PostgreSQL (Production)
**Best for:** Web apps, APIs, SaaS MVPs with 100-10K daily users.

```
my-app/
├── .replit
├── replit.nix
├── package.json
├── src/
│   ├── index.ts          # Express entry point
│   ├── config.ts          # Environment + secrets validation
│   ├── routes/
│   │   ├── api.ts         # Business logic
│   │   ├── auth.ts        # Replit Auth integration
│   │   └── health.ts      # Health check
│   ├── services/
│   │   ├── db.ts          # PostgreSQL pool
│   │   ├── kv.ts          # KV for cache/sessions
│   │   └── storage.ts     # Object Storage for files
│   └── middleware/
│       ├── auth.ts        # Auth header extraction
│       └── rateLimit.ts   # Rate limiting
└── tests/
```

```
Architecture:
  Client → Replit Proxy (Auth) → Express Server
                                      │
                    ┌─────────────────┤
                    │                 │
              PostgreSQL         KV Database
              (structured)       (cache/sessions)
                    │
              Object Storage
              (file uploads)
```

**Key decisions:**
- PostgreSQL for all structured data (users, posts, orders)
- KV Database for cache and session data only
- Object Storage for user uploads and backups
- Single Deployment (Autoscale or Reserved VM)

---

### Variant C: Multi-Service (Scale)
**Best for:** Production services with 10K+ daily users, background jobs, or real-time features.

```
Architecture:
  CDN (Cloudflare) → Replit Deployment 1: API Server
                            │
                      PostgreSQL (Replit)
                      Redis (Upstash — external)
                            │
                     Replit Deployment 2: Worker
                            │
                      Queue (Upstash Kafka — external)
                            │
                     Replit Deployment 3: Static Frontend
```

**Implementation:**
```markdown
Repl 1: my-app-api
  - Express/Fastify API server
  - Reserved VM deployment (always-on)
  - Handles authentication, CRUD operations
  - Publishes events to queue

Repl 2: my-app-worker
  - Background job processor
  - Reserved VM deployment (always-on)
  - Consumes events from queue
  - Handles: email sending, image processing, reports

Repl 3: my-app-frontend
  - React/Next.js frontend
  - Static deployment (free, CDN-backed)
  - Calls API server for data

Communication:
  - API to Worker: Upstash Kafka/Redis queues
  - Frontend to API: REST/GraphQL over HTTPS
  - Shared state: PostgreSQL + Redis
```

**When to use external services:**
| Service | Replit-native | External (Recommended at Scale) |
|---------|---------------|--------------------------------|
| Database | Replit PostgreSQL | Neon, Supabase, PlanetScale |
| Cache | Replit KV (50 MiB limit) | Upstash Redis |
| Queue | None built-in | Upstash Kafka, BullMQ |
| Storage | Object Storage | Cloudflare R2, AWS S3 |
| Search | None built-in | Algolia, Meilisearch |

---

### Variant D: Static + API Split
**Best for:** Frontend-heavy apps with a lightweight API backend.

```
Architecture:
  Client → Replit Static Deployment (React/Vue/Svelte)
              │
              └──→ Replit Autoscale Deployment (API)
                        │
                   PostgreSQL
```

```toml
# Frontend Repl .replit
[deployment]
deploymentTarget = "static"
publicDir = "dist"
build = ["sh", "-c", "npm ci && npm run build"]
```

```toml
# API Repl .replit
[deployment]
deploymentTarget = "autoscale"
run = ["sh", "-c", "node dist/index.js"]
build = ["sh", "-c", "npm ci && npm run build"]
```

**Benefit:** Frontend is free (Static deployment), API only charges when receiving requests (Autoscale).

## Growth Path
```
Single-File → Modular App → Multi-Service
   │                │              │
   │    Add PostgreSQL    Add Worker + Queue
   │    Add Auth          Add CDN
   │    Add Storage       Add Redis
   │                      Split frontend
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| KV database full | Over 50 MiB limit | Migrate to PostgreSQL |
| Container sleeping | Free plan / no deployment | Use Autoscale or Reserved VM |
| Cross-service latency | Multiple Repls communicating | Use external queue, not HTTP polling |
| Static deploy stale | Cache not cleared | Redeploy or add cache-busting |

## Resources
- [Replit Deployments](https://docs.replit.com/hosting/deployments)
- [Replit Database Options](https://docs.replit.com/category/storage-and-databases)
- [Upstash (Redis/Kafka)](https://upstash.com)
- [Neon (PostgreSQL)](https://neon.tech)

## Next Steps
For known pitfalls at each scale, see `replit-known-pitfalls`.
