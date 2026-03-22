# Klaviyo Skill Pack

> 24 production-grade Claude Code skills for Klaviyo email marketing, CDP, and customer engagement API integration.

Real `klaviyo-api` SDK code. Real `a.klaviyo.com/api/*` endpoints. Real `ApiKeySession` + `ProfilesApi` / `EventsApi` / `ListsApi` patterns. Covers profiles, events, lists, segments, campaigns, flows, webhooks, GDPR deletion, and the full operational stack from install to incident response.

**Links:** [Klaviyo API Reference](https://developers.klaviyo.com/en/reference/api_overview) | [klaviyo-api npm](https://www.npmjs.com/package/klaviyo-api) | [Tons of Skills](https://tonsofskills.com)

---

## Installation

```bash
/plugin install klaviyo-pack@claude-code-plugins-plus
```

## What's Inside

### Standard Skills (S01-S12)

| # | Skill | What It Does |
|---|-------|-------------|
| S01 | `klaviyo-install-auth` | Install `klaviyo-api` SDK, configure `ApiKeySession`, verify connection to `a.klaviyo.com/api/accounts/` |
| S02 | `klaviyo-hello-world` | Create a profile, track an event, query it back -- complete runnable script |
| S03 | `klaviyo-local-dev-loop` | Project structure, vitest mocks for `ProfilesApi`/`EventsApi`, integration test gating |
| S04 | `klaviyo-sdk-patterns` | Singleton sessions, type-safe wrappers, cursor pagination, multi-tenant factory |
| S05 | `klaviyo-core-workflow-a` | Profiles, lists, subscriptions: `createOrUpdateProfile`, `subscribeProfiles`, email+SMS consent |
| S06 | `klaviyo-core-workflow-b` | Event tracking, segments, campaigns: `createEvent`, `createCampaign`, `assignTemplateToCampaignMessage` |
| S07 | `klaviyo-common-errors` | Real 400/401/403/404/409/429/5xx error payloads with Klaviyo-specific fixes |
| S08 | `klaviyo-debug-bundle` | Shell script + programmatic debug info collector with PII redaction |
| S09 | `klaviyo-rate-limits` | 75 req/s burst + 700 req/min steady limits, `Retry-After` header handling, `p-queue` |
| S10 | `klaviyo-security-basics` | API key types (`pk_*` vs public), HMAC-SHA256 webhook verification, key rotation |
| S11 | `klaviyo-prod-checklist` | Pre-flight validation, health check endpoint, alert thresholds, rollback procedures |
| S12 | `klaviyo-upgrade-migration` | SDK version upgrades (`ConfigWrapper` to `ApiKeySession`), API revision timeline |

### Pro Skills (P13-P18)

| # | Skill | What It Does |
|---|-------|-------------|
| P13 | `klaviyo-ci-integration` | GitHub Actions workflows with mocked unit tests + live integration tests |
| P14 | `klaviyo-deploy-integration` | Vercel, Fly.io, Cloud Run deployments with secrets management |
| P15 | `klaviyo-webhooks-events` | Webhook API for topic subscriptions, HMAC verification, idempotency with Redis |
| P16 | `klaviyo-performance-tuning` | Sparse fieldsets, LRU caching, DataLoader batching, cursor pagination |
| P17 | `klaviyo-cost-tuning` | Active profile billing model, unengaged suppression, event sampling, sunset flows |
| P18 | `klaviyo-reference-architecture` | Layered project structure, `ProfileSyncService`, `EventTracker`, data flow diagrams |

### Flagship Skills (F19-F24)

| # | Skill | What It Does |
|---|-------|-------------|
| F19 | `klaviyo-multi-env-setup` | Per-environment API keys, GCP/AWS/Vault secrets, production guards, startup validation |
| F20 | `klaviyo-observability` | Prometheus metrics, OpenTelemetry tracing, pino structured logging, Grafana panels |
| F21 | `klaviyo-incident-runbook` | Quick triage script, decision tree, 401/429/5xx playbooks, postmortem template |
| F22 | `klaviyo-data-handling` | Data Privacy API (`requestProfileDeletion`), GDPR DSAR, PII redaction, consent management |
| F23 | `klaviyo-enterprise-rbac` | API key scoping by role, OAuth app flow, per-service keys, permission middleware |
| F24 | `klaviyo-migration-deep-dive` | v1/v2 field mapping, competitor import (Mailchimp), strangler fig pattern, validation |

## Key API Patterns

```typescript
import { ApiKeySession, ProfilesApi, EventsApi, ProfileEnum } from 'klaviyo-api';

const session = new ApiKeySession(process.env.KLAVIYO_PRIVATE_KEY!);
const profilesApi = new ProfilesApi(session);
const eventsApi = new EventsApi(session);

// Upsert a profile
await profilesApi.createOrUpdateProfile({
  data: {
    type: ProfileEnum.Profile,
    attributes: { email: 'user@example.com', firstName: 'Jane' },
  },
});

// Track an event (triggers flows)
await eventsApi.createEvent({
  data: {
    type: 'event',
    attributes: {
      metric: { data: { type: 'metric', attributes: { name: 'Placed Order' } } },
      profile: { data: { type: 'profile', attributes: { email: 'user@example.com' } } },
      properties: { orderId: 'ORD-123' },
      value: 99.99,
      time: new Date().toISOString(),
    },
  },
});
```

## SDK Conventions

| Convention | Detail |
|-----------|--------|
| Package | `klaviyo-api` (not `@klaviyo/sdk`) |
| Auth | `new ApiKeySession('pk_***')` |
| Response | `response.body.data` |
| Properties | camelCase (`firstName`, not `first_name`) |
| Rate limits | 75 req/s burst, 700 req/min steady |
| On 429 | Honor `Retry-After` header (integer seconds) |
| API base | `https://a.klaviyo.com/api/` |
| Revision | `2024-10-15` (supported until Oct 2026) |

## License

MIT
