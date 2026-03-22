---
name: customerio-reference-architecture
description: |
  Implement Customer.io enterprise reference architecture.
  Use when designing integration layers, event-driven architectures,
  or enterprise-grade Customer.io setups.
  Trigger: "customer.io architecture", "customer.io design",
  "customer.io enterprise", "customer.io integration pattern".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Glob, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, customer-io, architecture, enterprise]

---
# Customer.io Reference Architecture

## Overview

Enterprise-grade reference architecture for Customer.io: a service layer separating Track and App API concerns, event-driven processing with message queues, repository pattern for user-to-CIO sync, webhook event bus, and infrastructure as code.

## Architecture Principles

1. **Two Clients, Two Concerns** — `TrackClient` for behavioral data in, `APIClient` for messages out
2. **Event-Driven** — Message queues decouple your app from Customer.io API availability
3. **Idempotent Operations** — All writes safely retryable via content hashing
4. **Service Layer** — Business logic never calls Customer.io SDK directly
5. **Observability** — Every operation emits timing and error metrics

## Architecture Diagram

```
┌─────────────┐    ┌───────────────────┐    ┌──────────────┐
│ Application │───>│ MessagingService  │───>│ Track API    │
│ Routes      │    │ (service layer)   │    │ identify()   │
└─────────────┘    │                   │    │ track()      │
                   │ - identify users  │    └──────────────┘
                   │ - track events    │
                   │ - send txn emails │    ┌──────────────┐
                   │                   │───>│ App API      │
                   └───────────────────┘    │ sendEmail()  │
                          │                 │ broadcast()  │
                          │                 └──────────────┘
                          v
                   ┌───────────────────┐
                   │ Event Queue       │    ┌──────────────┐
                   │ (Redis/Kafka)     │───>│ DLQ          │
                   │ for reliability   │    │ (failures)   │
                   └───────────────────┘    └──────────────┘

┌─────────────┐    ┌───────────────────┐    ┌──────────────┐
│ Customer.io │───>│ Webhook Handler   │───>│ BigQuery     │
│ Webhooks    │    │ HMAC verification │    │ (analytics)  │
└─────────────┘    │ Event routing     │    └──────────────┘
```

## Instructions

### Step 1: Core Service Layer

```typescript
// services/messaging-service.ts
import { EventEmitter } from "events";
import { TrackClient, APIClient, SendEmailRequest, RegionUS, RegionEU } from "customerio-node";

interface MessagingConfig {
  siteId: string;
  trackApiKey: string;
  appApiKey: string;
  region: "us" | "eu";
}

export class MessagingService extends EventEmitter {
  private track: TrackClient;
  private app: APIClient;

  constructor(config: MessagingConfig) {
    super();
    const region = config.region === "eu" ? RegionEU : RegionUS;
    this.track = new TrackClient(config.siteId, config.trackApiKey, { region });
    this.app = new APIClient(config.appApiKey, { region });
  }

  async identifyUser(userId: string, attrs: Record<string, any>): Promise<void> {
    const start = Date.now();
    try {
      await this.track.identify(userId, {
        ...attrs,
        last_seen_at: Math.floor(Date.now() / 1000),
      });
      this.emit("identify", { userId, latencyMs: Date.now() - start });
    } catch (err) {
      this.emit("error", { operation: "identify", userId, err });
      throw err;
    }
  }

  async trackEvent(
    userId: string,
    name: string,
    data?: Record<string, any>
  ): Promise<void> {
    const start = Date.now();
    try {
      await this.track.track(userId, { name, data });
      this.emit("track", { userId, name, latencyMs: Date.now() - start });
    } catch (err) {
      this.emit("error", { operation: "track", userId, name, err });
      throw err;
    }
  }

  async sendTransactional(
    to: string,
    templateId: string,
    data: Record<string, any>,
    identifiers?: { id?: string; email?: string }
  ): Promise<{ delivery_id: string }> {
    const start = Date.now();
    try {
      const request = new SendEmailRequest({
        to,
        transactional_message_id: templateId,
        message_data: data,
        identifiers,
      });
      const result = await this.app.sendEmail(request);
      this.emit("transactional", { to, templateId, latencyMs: Date.now() - start });
      return result;
    } catch (err) {
      this.emit("error", { operation: "transactional", to, templateId, err });
      throw err;
    }
  }

  async triggerBroadcast(
    broadcastId: number,
    data: Record<string, any>,
    options: { segment?: { id: number }; emails?: string[]; ids?: string[] }
  ): Promise<void> {
    await this.app.triggerBroadcast(broadcastId, data, options);
    this.emit("broadcast", { broadcastId });
  }

  async suppressUser(userId: string): Promise<void> {
    await this.track.suppress(userId);
  }

  async deleteUser(userId: string): Promise<void> {
    await this.track.destroy(userId);
  }
}
```

### Step 2: Queue-Backed Reliability Layer

```typescript
// services/messaging-queue.ts
// Wraps MessagingService with queue-based reliability

import { Queue, Worker, Job } from "bullmq";
import { MessagingService } from "./messaging-service";

const REDIS_URL = process.env.REDIS_URL ?? "redis://localhost:6379";

const identifyQueue = new Queue("cio:identify", { connection: { url: REDIS_URL } });
const trackQueue = new Queue("cio:track", { connection: { url: REDIS_URL } });
const transactionalQueue = new Queue("cio:transactional", {
  connection: { url: REDIS_URL },
});

export class QueuedMessagingService {
  constructor(private messaging: MessagingService) {}

  async enqueueIdentify(
    userId: string,
    attrs: Record<string, any>
  ): Promise<void> {
    await identifyQueue.add("identify", { userId, attrs }, {
      attempts: 3,
      backoff: { type: "exponential", delay: 2000 },
    });
  }

  async enqueueTrack(
    userId: string,
    name: string,
    data?: Record<string, any>
  ): Promise<void> {
    await trackQueue.add("track", { userId, name, data }, {
      attempts: 3,
      backoff: { type: "exponential", delay: 2000 },
    });
  }

  startWorkers(): void {
    new Worker("cio:identify", async (job: Job) => {
      await this.messaging.identifyUser(job.data.userId, job.data.attrs);
    }, { connection: { url: REDIS_URL }, concurrency: 10 });

    new Worker("cio:track", async (job: Job) => {
      await this.messaging.trackEvent(
        job.data.userId,
        job.data.name,
        job.data.data
      );
    }, { connection: { url: REDIS_URL }, concurrency: 10 });

    new Worker("cio:transactional", async (job: Job) => {
      await this.messaging.sendTransactional(
        job.data.to,
        job.data.templateId,
        job.data.data,
        job.data.identifiers
      );
    }, { connection: { url: REDIS_URL }, concurrency: 5 });
  }
}
```

### Step 3: Repository Pattern

```typescript
// repositories/user-messaging-repo.ts
// Syncs your user database with Customer.io profiles

import { MessagingService } from "../services/messaging-service";

interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  plan: string;
  createdAt: Date;
  preferences: { marketing: boolean; transactional: boolean };
}

export class UserMessagingRepository {
  constructor(private messaging: MessagingService) {}

  async syncUser(user: User): Promise<void> {
    if (!user.preferences.transactional && !user.preferences.marketing) {
      // User has opted out of all messaging — suppress
      await this.messaging.suppressUser(user.id);
      return;
    }

    await this.messaging.identifyUser(user.id, {
      email: user.email,
      first_name: user.firstName,
      last_name: user.lastName,
      plan: user.plan,
      created_at: Math.floor(user.createdAt.getTime() / 1000),
      marketing_opt_in: user.preferences.marketing,
      transactional_opt_in: user.preferences.transactional,
    });
  }

  async onUserDeleted(userId: string): Promise<void> {
    await this.messaging.suppressUser(userId);
    await this.messaging.deleteUser(userId);
  }
}
```

### Step 4: Infrastructure as Code (Terraform)

```hcl
# terraform/customerio.tf

# Secrets
resource "google_secret_manager_secret" "cio_site_id" {
  secret_id = "customerio-site-id"
  replication { auto {} }
}

resource "google_secret_manager_secret" "cio_track_key" {
  secret_id = "customerio-track-api-key"
  replication { auto {} }
}

resource "google_secret_manager_secret" "cio_app_key" {
  secret_id = "customerio-app-api-key"
  replication { auto {} }
}

# Cloud Run service
resource "google_cloud_run_v2_service" "cio_service" {
  name     = "customerio-service"
  location = "us-central1"

  template {
    scaling {
      min_instance_count = 1
      max_instance_count = 10
    }

    containers {
      image = "gcr.io/${var.project_id}/customerio-service:latest"

      env {
        name  = "CUSTOMERIO_REGION"
        value = "us"
      }

      env {
        name = "CUSTOMERIO_SITE_ID"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.cio_site_id.secret_id
            version = "latest"
          }
        }
      }

      resources {
        limits = { cpu = "1", memory = "512Mi" }
      }
    }
  }
}
```

## Error Handling

| Issue | Solution |
|-------|----------|
| Queue worker failure | BullMQ retries with exponential backoff; check DLQ |
| Service layer error | EventEmitter "error" event logged + alerted |
| Secret rotation | Update Secret Manager version, redeploy |
| Cross-service consistency | Use idempotent operations (identify is idempotent) |

## Resources

- [Customer.io API Overview](https://docs.customer.io/integrations/api/customerio-apis/)
- [Track API Reference](https://docs.customer.io/integrations/api/track/)
- [App API Reference](https://docs.customer.io/integrations/api/app/)
- [BullMQ Documentation](https://bullmq.io/)

## Next Steps

After implementing architecture, proceed to `customerio-multi-env-setup` for multi-environment configuration.
