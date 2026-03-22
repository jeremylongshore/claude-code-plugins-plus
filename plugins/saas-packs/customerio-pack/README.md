# Customer.io Skill Pack

> 24 production-grade Claude Code skills for Customer.io marketing automation (email, push, SMS, in-app messaging)

Build, debug, and scale Customer.io integrations with real `customerio-node` SDK code -- `TrackClient` for behavioral data, `APIClient` for transactional messages and broadcasts, webhook handling, and enterprise reliability patterns.

## Installation

```bash
/plugin install customerio-pack@claude-code-plugins-plus
```

## What You Get

Real Customer.io code in every skill -- not stubs. Each skill contains working TypeScript using the actual `customerio-node` SDK (`TrackClient`, `APIClient`, `SendEmailRequest`, `RegionUS`/`RegionEU`), production error handling, and Customer.io-specific gotchas.

## Skills (24)

### Standard (S01-S12) -- Setup Through Production

| # | Skill | What It Does |
|---|-------|-------------|
| S01 | `customerio-install-auth` | Install `customerio-node`, configure Track API + App API credentials, verify connection |
| S02 | `customerio-hello-world` | First `identify()` + `track()` + `sendEmail()` -- end-to-end in one script |
| S03 | `customerio-local-dev-loop` | Dry-run client, vitest mocks, environment isolation, dev workspace prefixing |
| S04 | `customerio-sdk-patterns` | Type-safe event unions, retry with backoff, batch queue, singleton factory |
| S05 | `customerio-primary-workflow` | Event taxonomy, MessagingService, campaign trigger flow, Liquid template variables |
| S06 | `customerio-core-feature` | Transactional email/push, API-triggered broadcasts, segments, user merge, suppress/delete |
| S07 | `customerio-common-errors` | HTTP status codes, auth debugging, timestamp pitfalls, 429 backoff, delivery checklist |
| S08 | `customerio-debug-bundle` | API connectivity test, user investigation script, env info collector, support report |
| S09 | `customerio-rate-limits` | Token bucket, exponential backoff + jitter, rate-limited client, p-queue integration |
| S10 | `customerio-security-basics` | Secrets manager, PII sanitization, HMAC webhook verification, GDPR deletion |
| S11 | `customerio-prod-checklist` | Credential audit, deliverability (SPF/DKIM/DMARC), smoke tests, staged rollout plan |
| S12 | `customerio-upgrade-migration` | Legacy `CustomerIO` to `TrackClient` migration, version check, staged rollout with feature flags |

### Pro (P13-P18) -- DevOps and Operations

| # | Skill | What It Does |
|---|-------|-------------|
| P13 | `customerio-ci-integration` | GitHub Actions workflow, test fixtures with cleanup, integration tests, pre-commit hooks |
| P14 | `customerio-deploy-pipeline` | Cloud Run, Vercel, Lambda, Kubernetes deployments with health checks and blue-green |
| P15 | `customerio-webhooks-events` | Reporting webhook receiver, HMAC-SHA256 verification, bounce/spam handling, BigQuery streaming |
| P16 | `customerio-performance-tuning` | Connection pooling, identify dedup cache, batch processor, fire-and-forget, regional routing |
| P17 | `customerio-cost-tuning` | Profile audit, inactive user cleanup, event deduplication, sampling, usage monitoring |
| P18 | `customerio-reference-architecture` | Service layer, BullMQ queue workers, repository pattern, Terraform IaC |

### Flagship (F19-F24) -- Enterprise Scale

| # | Skill | What It Does |
|---|-------|-------------|
| F19 | `customerio-multi-env-setup` | Dev/staging/prod workspace isolation, typed config, Kubernetes overlays, CI promotion |
| F20 | `customerio-observability` | Prometheus metrics, instrumented client, pino structured logging, Grafana dashboard, alerting rules |
| F21 | `customerio-advanced-troubleshooting` | Debug client, user investigation, campaign debugging, network diagnostics, incident runbooks (P1-P4) |
| F22 | `customerio-reliability-patterns` | Circuit breaker, retry + jitter, BullMQ fallback queue, idempotency guard, graceful degradation |
| F23 | `customerio-load-scale` | k6 load tests, queue-based architecture, Kubernetes HPA, Bottleneck rate limiting |
| F24 | `customerio-known-pitfalls` | 12 common mistakes with wrong/right code: timestamps, auth keys, event naming, PII, singletons |

## Customer.io API Coverage

| API Surface | SDK Class | Skills Using It |
|-------------|-----------|----------------|
| Track API (identify, track, suppress, destroy, merge) | `TrackClient` | S01-S12, P16-P18, F19-F24 |
| App API (transactional email/push, broadcasts) | `APIClient` | S01, S02, S06, P15, P18 |
| Reporting Webhooks (delivery events) | HTTP receiver | P15, F21, F22 |

## Quick Start

```typescript
import { TrackClient, APIClient, SendEmailRequest, RegionUS } from "customerio-node";

// Track API -- identify users and track events
const cio = new TrackClient(siteId, trackApiKey, { region: RegionUS });
await cio.identify("user-123", { email: "jane@example.com", plan: "pro" });
await cio.track("user-123", { name: "signed_up", data: { method: "google" } });

// App API -- send transactional messages
const api = new APIClient(appApiKey, { region: RegionUS });
await api.sendEmail(new SendEmailRequest({
  to: "jane@example.com",
  transactional_message_id: "1",
  message_data: { name: "Jane" },
  identifiers: { id: "user-123" },
}));
```

## Key Concepts

- **Two API keys**: Track API Key (identify/track) and App API Key (transactional/broadcasts) -- different credentials
- **Timestamps**: Always Unix **seconds** (`Math.floor(Date.now() / 1000)`), never milliseconds
- **Regions**: US (`RegionUS`) or EU (`RegionEU`) -- must match your account
- **Event names**: `snake_case`, case-sensitive, must match campaign triggers exactly
- **Identify before track**: Always call `identify()` before `track()` for a user

## License

MIT
