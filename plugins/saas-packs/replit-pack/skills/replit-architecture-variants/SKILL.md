---
name: replit-architecture-variants
description: |
  Choose and implement Replit validated architecture blueprints for different scales.
  Use when designing new Replit integrations, choosing between monolith/service/microservice
  architectures, or planning migration paths for Replit applications.
  Trigger with phrases like "replit architecture", "replit blueprint",
  "how to structure replit", "replit project layout", "replit microservice".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Replit Architecture Variants

## Overview
Application architectures on Replit at different scales. Replit's container model, built-in database, and Deployments feature support architectures from simple scripts to production web services.

## Prerequisites
- Replit account (Free, Hacker, or Pro)
- Understanding of Replit's container lifecycle
- Awareness of plan-specific resource limits

## Instructions

### Step 1: Single-File Script (Prototype)

**Best for:** Scripts, bots, automation, learning.

```python
# main.py - everything in one file
from flask import Flask
from replit import db

app = Flask(__name__)

@app.route('/')
def home():
    count = db.get("visits") or 0
    db["visits"] = count + 1
    return f"Visit #{count + 1}"

app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 3000)))
```

**Limits:** Sleeps after inactivity (free plan). 512MB RAM. Replit DB (50MB).

### Step 2: Modular App with External DB (Production)

**Best for:** Web apps, APIs, 100-10K daily users.

```
Replit Deployment -> External PostgreSQL (Neon/Supabase)
                  -> External Redis (Upstash)
                  -> External Storage (S3/Replit Object Storage)
```

```python
# Structured project layout
# main.py -> routes/ -> services/ -> models/
import os
from flask import Flask
from sqlalchemy import create_engine

app = Flask(__name__)
engine = create_engine(os.environ["DATABASE_URL"])  # External Postgres

# Use Replit Deployments for always-on
# Use external DB for persistence beyond container lifecycle
```

### Step 3: Multi-Service with Replit Deployments (Scale)

**Best for:** Production services, microservices, 10K+ daily users.

```
CDN (Cloudflare) -> Replit Deployment (API)
                         |
                    External DB (Neon Postgres)
                    External Cache (Upstash Redis)
                    External Queue (Upstash Kafka)
                         |
                    Replit Deployment (Worker)
```

```python
# API service (Replit Deployment 1)
# Worker service (Replit Deployment 2)
# Each in its own Repl with own Deployment
# Communicate via shared database/queue
```

## Decision Matrix

| Factor | Single-File | Modular + External DB | Multi-Service |
|--------|------------|----------------------|---------------|
| Users | Prototype | 100-10K/day | 10K+/day |
| Database | Replit DB | External Postgres | External + cache |
| Persistence | Ephemeral | Durable | Durable |
| Cost | Free | $7-20/mo | $20+/mo |
| Always-on | No (free) | Yes (Deployment) | Yes |

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Data loss | Using filesystem/Replit DB | Migrate to external database |
| Container sleeping | Free plan limitations | Use Deployments or keep-alive |
| Memory limit | Large in-memory datasets | Stream data, use external storage |

## Resources
- [Replit Deployments](https://docs.replit.com/hosting/deployments)
- [Replit Database Options](https://docs.replit.com/hosting/databases)
