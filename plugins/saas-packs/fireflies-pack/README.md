# Fireflies.ai Skill Pack

> 24 production-ready skills for the Fireflies.ai GraphQL API -- transcript retrieval, AskFred AI, webhook processing, meeting analytics, and enterprise access control.

Fireflies.ai is an AI meeting notetaker that auto-joins video calls (Zoom, Google Meet, Teams), generates speaker-diarized transcripts, extracts action items, and provides AI-powered Q&A via AskFred. This skill pack covers the entire Fireflies GraphQL API surface at `https://api.fireflies.ai/graphql`.

## Installation

```bash
/plugin install fireflies-pack@claude-code-plugins-plus
```

## What You Get

Every skill uses **real Fireflies.ai GraphQL queries and mutations** -- no fake SDKs, no placeholder code. Copy-paste ready.

**API coverage:** `transcript`, `transcripts`, `user`, `users`, `channels`, `bites`, `apps`, `askfred_threads` queries. `uploadAudio`, `addToLiveMeeting`, `createBite`, `shareMeeting`, `updateMeetingPrivacy`, `updateMeetingChannel`, `deleteTranscript`, `createAskFredThread`, `continueAskFredThread`, `setUserRole` mutations. Webhook signature verification with HMAC-SHA256.

## Skills Included

### Standard Skills (S01-S12)
| Skill | What It Does |
|-------|-------------|
| `fireflies-install-auth` | Configure GraphQL API auth, verify connectivity with `user` query |
| `fireflies-hello-world` | First queries: list users, fetch transcripts, read summaries |
| `fireflies-local-dev-loop` | Project structure, fixture recording, mock client, vitest setup |
| `fireflies-sdk-patterns` | Typed GraphQL client class, singleton, multi-tenant factory, Zod validation |
| `fireflies-core-workflow-a` | Transcript retrieval: sentences, speakers, analytics, AI filters |
| `fireflies-core-workflow-b` | Search transcripts, AskFred AI Q&A, cross-meeting analytics |
| `fireflies-common-errors` | All error codes: `auth_failed`, `too_many_requests`, `require_ai_credits`, deprecated fields |
| `fireflies-debug-bundle` | Diagnostic script: API connectivity, account info, calendar sync, redacted bundle |
| `fireflies-rate-limits` | Per-plan limits (50/day vs 60/min), exponential backoff, PQueue, daily budget tracker |
| `fireflies-security-basics` | API key rotation, webhook HMAC-SHA256 verification, privacy levels, pre-commit hook |
| `fireflies-prod-checklist` | Health check endpoint, alerting thresholds, deployment verification |
| `fireflies-upgrade-migration` | Deprecated field scanner, schema introspection, query pattern updates |

### Pro Skills (P13-P18)
| Skill | What It Does |
|-------|-------------|
| `fireflies-ci-integration` | GitHub Actions workflow, mock-based unit tests, live API integration tests |
| `fireflies-deploy-integration` | Deploy webhook receivers to Vercel, Docker, Cloud Run with secret management |
| `fireflies-webhooks-events` | HMAC signature verification, `Transcription completed` event processing, per-upload webhooks |
| `fireflies-performance-tuning` | Field selection optimization, LRU/Redis caching, batch processing, webhook cache warming |
| `fireflies-cost-tuning` | Seat utilization audit via API, selective recording, plan right-sizing, storage cleanup |
| `fireflies-reference-architecture` | Event-driven pipeline: webhook -> transcript store -> action items -> CRM -> analytics |

### Flagship Skills (F19-F24)
| Skill | What It Does |
|-------|-------------|
| `fireflies-multi-env-setup` | Per-environment config (dev/staging/prod), GCP Secret Manager, Zod startup validation |
| `fireflies-observability` | Prometheus metrics, health probes, webhook queue depth, seat utilization tracking |
| `fireflies-incident-runbook` | Triage script, decision tree by error code, remediation procedures, postmortem template |
| `fireflies-data-handling` | Export (JSON/text/SRT/CSV), PII redaction, retention policies, GDPR data subject requests |
| `fireflies-enterprise-rbac` | Workspace roles, channels, privacy levels, `shareMeeting`/`revokeSharedMeetingAccess`, audit |
| `fireflies-migration-deep-dive` | `uploadAudio` batch import, authenticated URLs, direct upload, adapter pattern, validation |

## Key API Details

| Detail | Value |
|--------|-------|
| Endpoint | `https://api.fireflies.ai/graphql` |
| Auth | `Authorization: Bearer <API_KEY>` |
| Protocol | GraphQL (POST only) |
| Rate limits | Free/Pro: 50/day, Business/Enterprise: 60/min |
| Webhook event | `Transcription completed` |
| Webhook auth | HMAC-SHA256 via `x-hub-signature` header |
| Supported platforms | Zoom, Google Meet, Microsoft Teams |

## Usage

Skills trigger automatically when you discuss Fireflies.ai topics:

- "Help me set up the Fireflies API" -- triggers `fireflies-install-auth`
- "Fetch my recent meeting transcripts" -- triggers `fireflies-core-workflow-a`
- "Search meetings for quarterly review" -- triggers `fireflies-core-workflow-b`
- "Set up a webhook for transcript notifications" -- triggers `fireflies-webhooks-events`
- "Upload a recording to Fireflies" -- triggers `fireflies-migration-deep-dive`
- "Ask Fred about my last meeting" -- triggers `fireflies-core-workflow-b`

## License

MIT
