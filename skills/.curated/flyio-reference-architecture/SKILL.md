---
name: flyio-reference-architecture
description: 'Implement Fly.io reference architecture with multi-region apps, Postgres,

  Redis, background workers, and private networking.

  Trigger: "fly.io architecture", "fly.io system design", "fly.io multi-region".

  '
allowed-tools: Read, Write, Edit
version: 1.7.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- edge-compute
- flyio
compatibility: Designed for Claude Code
---
# Fly.io Reference Architecture

## Overview

Production architecture for Fly.io: multi-region web tier, Postgres with read replicas, Redis for caching, background workers, and private networking.

## Prerequisites

- A documented data-flow inventory, trust boundaries, ownership, region/retention choices, and disaster-recovery objectives.
- Separate scoped identities for deployment, runtime, database, worker, and observability systems.

## Instructions

1. Place public ingress, private services, storage, workers, and observability behind explicit network and identity boundaries.
2. Define data locality, replication, backup, access, and recovery behavior before creating additional regions or consumers.
3. Use staged deployment, health checks, redacted telemetry, and an independently tested rollback per service.
4. Validate architecture changes with synthetic traffic and ensure a failure in one region cannot leak secrets or corrupt cross-region state.

## Output

Maintain an architecture decision record with components, trust boundaries, data locations, identities, health/rollback controls, owners, and recovery evidence. Do not include secrets or customer data.

## Error Handling

- Isolate an unhealthy region or consumer and preserve a safe primary path while recovery proceeds.
- Quarantine unexpected cross-region writes or permission failures for review.
- Restore the previous routing/configuration before replaying queued work.

## Examples

Deploy a fictional workload to a staging primary and replica region, deny the worker access to public ingress secrets, and simulate a regional health failure. Verify traffic stays on the healthy route and rollback does not replay writes.

## Architecture

```
           ┌─────────── Fly.io Anycast DNS ──────────┐
           │                                          │
    ┌──────▼──────┐  ┌──────────────┐  ┌─────────────▼───┐
    │  Web (iad)  │  │  Web (lhr)   │  │   Web (nrt)     │
    │  shared-1x  │  │  shared-1x   │  │   shared-1x     │
    └──────┬──────┘  └──────┬───────┘  └────────┬────────┘
           │                │                    │
    ───────┴────────────────┴────────────────────┴─── .internal DNS
           │                │                    │
    ┌──────▼──────┐  ┌──────▼───────┐  ┌────────▼────────┐
    │ Postgres    │  │ Postgres     │  │   Redis          │
    │ Primary     │  │ Replica      │  │   (upstash.io)   │
    │ (iad)       │  │ (lhr)        │  │                  │
    └─────────────┘  └──────────────┘  └──────────────────┘
           │
    ┌──────▼──────┐
    │  Worker     │
    │  (iad)      │
    │  shared-1x  │
    └─────────────┘
```

## Setup Commands

```bash
# 1. Web app — multi-region
fly launch --name my-web --region iad
fly scale count 1 --region lhr
fly scale count 1 --region nrt

# 2. Postgres with replica
fly postgres create --name my-db --region iad
fly postgres attach my-db -a my-web
# Add read replica in Europe
fly machine clone <primary-machine-id> --region lhr -a my-db

# 3. Background worker (same codebase, different process)
fly launch --name my-worker --region iad --no-deploy
# fly.toml for worker: no [http_service], use [processes]

# 4. All communicate via .internal DNS
# my-db.internal:5432 (Postgres)
# my-web.internal:3000 (internal API)
```

## fly.toml Configurations

### Web App

```toml
app = "my-web"
primary_region = "iad"

[http_service]
  internal_port = 3000
  force_https = true
  auto_stop_machines = "suspend"
  min_machines_running = 1

[[vm]]
  cpu_kind = "shared"
  cpus = 1
  memory = "512mb"
```

### Background Worker

```toml
app = "my-worker"
primary_region = "iad"

[processes]
  worker = "node dist/worker.js"

# No [http_service] — worker doesn't serve HTTP

[[vm]]
  cpu_kind = "shared"
  cpus = 1
  memory = "512mb"
```

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Web tier | 3 regions | Low latency for global users |
| Database | Fly Postgres + replica | Read replicas near users |
| Cache | Upstash Redis (or Fly Redis) | Managed, multi-region |
| Workers | Separate Fly app | Independent scaling |
| Networking | 6PN (.internal DNS) | Zero-trust, no public exposure |
| Storage | Fly Volumes (NVMe) | Fast, region-local |

## Resources

- [Fly.io Docs](https://fly.io/docs/)
- [Multi-Region Postgres](https://fly.io/docs/postgres/high-availability-and-global-replication/)
- [Private Networking](https://fly.io/docs/networking/private-networking/)
