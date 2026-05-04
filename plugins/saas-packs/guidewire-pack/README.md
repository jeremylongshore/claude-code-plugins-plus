# Guidewire Skill Pack

> 10 production-engineer Claude Code skills for Guidewire InsuranceSuite. Each skill addresses real Cloud API failure modes — token storms, checksum 409s, blocked binds, FNOL dedup, secret rotation — not tutorial walk-throughs.

## What This Is

A focused skill pack for engineers building, deploying, and operating Guidewire Cloud API integrations in production. Every skill is structured around the failure modes a working integration actually hits: token expiry storms during traffic spikes, checksum conflicts under concurrent edits, scope drift when a tenant admin reconfigures roles, FNOL duplication from multi-source intake, premium drift on mid-term endorsements, GCC slot promotion that breaks running policies, App Events that never fire because Gosu registration was missed.

This is the pack you reach for when "make a hello-world request" has been done two years ago and the question is "how do we run this at carrier scale without paging on-call every weekend."

**v2.0.0 (May 2026)** — full rebuild from v1's 24-skill scaffold to 10 production-focused skills, every one validated at A-grade (≥90/100) on the marketplace tier.

## Installation

```bash
/plugin install guidewire-pack@claude-code-plugins-plus
```

Or directly:

```bash
npm install @intentsolutionsio/guidewire-pack
```

## The 10 skills

| # | Skill | The production problem it solves |
|---|-------|----------------------------------|
| 1 | `guidewire-install-auth` | Production OAuth2 — token caching with proactive refresh, SOPS+age secret rotation, JVM private-CA trust store, scope-drift detection |
| 2 | `guidewire-sdk-patterns` | Cloud API client that survives 409 checksum conflicts, 429 with Retry-After honour, offsetToken pagination, Idempotency-Key for retry-safe writes |
| 3 | `guidewire-local-dev-loop` | Sub-90s Gosu iteration — what hot-reloads vs forces 5–15min restart, JDWP debugger, GUnit `--continuous` TDD cycle |
| 4 | `guidewire-core-workflow-a` | PolicyCenter pipeline (account→submission→quote→bind→issue→endorse→renew) including UW issue handling, quote expiry, premium drift, renewal window |
| 5 | `guidewire-core-workflow-b` | ClaimCenter pipeline (FNOL→reserve→payment→settle→close) including FNOL dedup, reserve-before-payment ordering, authorization tiers, reopen logic |
| 6 | `guidewire-security-and-rbac` | SOC 2 + NAIC posture — least-privilege roles, SOPS+age committed encrypted secrets, PII redaction at logger transport, integration audit trail, per-tenant isolation |
| 7 | `guidewire-observability-and-incident-response` | SLI/SLO design, burn-rate alerting, 5 triage trees (401/409/429/scope-drift/OOM), 5 recovery playbooks, post-incident review template |
| 8 | `guidewire-ci-cd-pipeline` | Gosu compile + GUnit gates, immutable config-package promotion through GCC slots, smoke + UAT regression gates, canary with traffic split, bound-state-aware rollback |
| 9 | `guidewire-webhooks-integrations` | App Events Gosu+Messaging.xml registration, consumer-side messageId dedup, out-of-order tolerance via deferred queue, checkpoint-based replay, back-pressure response |
| 10 | `guidewire-migration-and-upgrade` | On-prem→cloud cutover and version upgrades — customization inventory, rehearsal-driven cutover with quantitative abort criteria, post-cutover stabilization |

## Quality bar

Every skill in this pack ships at A-grade (≥90/100) on the Intent Solutions marketplace validator (`scripts/validate-skills-schema.py --marketplace`). Pack-wide:

- **10/10 A-grade**, average 95.9/100
- **Lowest 93/100**, well above the 90 floor
- **0 ERROR-level findings** across the pack
- Every skill has a `references/API_REFERENCE.md` deep-dive
- Every cross-reference points to a sibling that actually exists

## Key Guidewire concepts (refresher)

- **InsuranceSuite** — PolicyCenter (policy admin) + ClaimCenter (claims) + BillingCenter (billing)
- **Cloud API** — RESTful APIs with OAuth2 client-credentials auth via Guidewire Hub; runtime URLs on `*.guidewire.net`
- **Gosu** — JVM language for server-side business logic (rules, validations, App Event builders)
- **GCC** — Guidewire Cloud Console (`gcc.guidewire.com`) — tenant administration, app registration, deployment slots, audit
- **App Events** — typed business events fired by InsuranceSuite on entity-state transitions; routed to SQS/SNS/webhooks
- **Slots** — GCC's promotion mechanism (`dev`/`uat`/`prod`); config packages are deployed to slots, not built on the slot
- **Checksum** — every Cloud API resource carries one; PATCH/PUT must echo it for optimistic locking

## What's deliberately not in this pack (v2.0.0)

Cut from v1 because they were tutorial fluff or generic insurance 101:

- Hello-world / first-API-call walkthroughs
- Generic "common errors" lookup (folded into observability triage)
- Reference-architecture overview (architectural context, not a how-to)
- Generic data-handling (no Guidewire-specific automation value)

Deferred to v2.1+:

- `guidewire-performance-and-cost` — JVM tuning, Gosu Query API N+1 elimination, license utilization (deferred until validated against a real tenant by a Guidewire domain expert; current `calculateLicensingCost` patterns in v1 were unverifiable)

Treat the pack as the answer to "how do we run a Guidewire integration in production without setting fires" — not as the answer to "I have never used Guidewire, where do I start." For the latter, Guidewire's developer portal is the right starting point.

## About Guidewire

Guidewire is the leading platform for P&C (Property & Casualty) insurance carriers. As of May 2026, Guidewire does not ship an official MCP server, and there is no community MCP server in the public registry. The skills in this pack are the foundation for any future MCP layer around Guidewire's system of record.

## Resources

- [Guidewire Developer Portal](https://developer.guidewire.com/)
- [Cloud API Reference (PolicyCenter)](https://docs.guidewire.com/cloud/pc/202503/apiref/)
- [Cloud API Reference (ClaimCenter)](https://docs.guidewire.com/cloud/cc/202407/apiref/)
- [Gosu Language](https://gosu-lang.github.io/)
- [Guidewire Cloud Console](https://gcc.guidewire.com/)

## License

MIT
