# Grammarly Production Operator Pack

**v2.0.0** — five model-agnostic Agent Skills for safe Grammarly API operations:
access readiness, document evaluation, API reliability, content-transfer governance,
and license review.

> [!IMPORTANT]
> v2 replaces 24 documentation-style v1 skills whose examples included inaccurate or
> undocumented API contracts. The install slug stays `grammarly-pack`. Review the
> complete [v1 to v2 migration](#v1-to-v2-migration) before upgrading.

## Why this pack exists

The pack turns Grammarly's public developer contracts into reviewable operator
workflows. Four helpers are offline analyzers. The only network-capable helper is dry-run
by default and requires an exact content SHA-256 confirmation before it requests a token,
creates a job, uploads a document, or polls a result.

This is not a browser writing assistant and does not emulate Grammarly suggestions. It
does not invent sandbox, webhook, pricing, quota, account, usage, or direct-text APIs.

## Installation

Install the repository's plugin bundle in a compatible plugin host:

```bash
/plugin install grammarly-pack@claude-code-plugins-plus
```

The skill directories also follow the Agent Skills format and can be consumed by other
compatible hosts. Deterministic helpers require Python 3.10 or newer and use only the
standard library.

## The five skills

| Skill | Operator outcome | Network behavior |
|---|---|---|
| `grammarly-access-readiness` | Validate entitlement, operation selection, and least-privilege OAuth scopes without collecting credentials | Offline only |
| `grammarly-document-evaluator` | Dry-run or explicitly execute Writing Score, AI Detection, and Plagiarism document jobs | Dry-run by default; explicit confirmed execution |
| `grammarly-api-reliability` | Analyze metadata-only job receipts, statuses, rate-limit evidence, and bounded recovery | Offline only |
| `grammarly-data-safety-guardian` | Gate document-transfer manifests against consent, classification, format, size, and retention policy | Offline only |
| `grammarly-license-governor` | Produce a review-only inactivity candidate plan from sanitized license snapshots | Offline only; never deletes |

## Security invariants

- OAuth credentials come only from `GRAMMARLY_CLIENT_ID` and
  `GRAMMARLY_CLIENT_SECRET`; tools never accept or print secret values.
- Raw text, document previews, response bodies, bearer tokens, presigned URLs, emails,
  names, and raw license resource IDs are rejected from diagnostic inputs.
- Live document transfer requires a dry-run digest, upload-origin inspection, a READY
  data-safety manifest bound to both destinations, and explicit `--execute`.
- Job creation is not automatically retried because Grammarly does not document
  idempotency.
- Local polling caps are operator controls, not claims about Grammarly processing time.
- Failed or pending analysis is never replaced by a fabricated score.
- License governance emits candidates for human review and does not call DELETE APIs.
- Unknown endpoints, fields, statuses, scopes, or documentation conflicts fail closed.

## Official API surface

| Surface | Verified contract |
|---|---|
| OAuth | `POST https://auth.grammarly.com/v4/api/oauth2/token`, form-encoded client credentials plus comma-separated scopes |
| Writing Score | `/ecosystem/api/v2/scores`, create/upload/poll, scores on `0..1` |
| AI Detection (Beta) | `/ecosystem/api/v1/ai-detection`, create/upload/poll |
| Plagiarism Detection (Beta) | `/ecosystem/api/v1/plagiarism`, create/upload/poll |
| Analytics | `/ecosystem/api/v2/analytics/users/`, read-only and cursor-paginated |
| License Management | `/ecosystem/api/v1/users` and `/invitees`; v2 automation is analysis-only |

Contract evidence and known documentation ambiguities are recorded in
[`000-docs/002-RL-RSRC-grammarly-api-contract-audit.md`](000-docs/002-RL-RSRC-grammarly-api-contract-audit.md).

## v1 to v2 migration

Every removed ID has an explicit disposition in [`migration-map.json`](migration-map.json).

| v1 skill(s) | v2 destination |
|---|---|
| `grammarly-install-auth`, `grammarly-local-dev-loop`, `grammarly-sdk-patterns`, `grammarly-multi-env-setup`, `grammarly-deploy-integration`, `grammarly-ci-integration`, `grammarly-upgrade-migration`, `grammarly-migration-deep-dive` | `grammarly-access-readiness` |
| `grammarly-hello-world`, `grammarly-core-workflow-a`, `grammarly-core-workflow-b`, `grammarly-data-handling` | `grammarly-document-evaluator` |
| `grammarly-common-errors`, `grammarly-debug-bundle`, `grammarly-rate-limits`, `grammarly-observability`, `grammarly-incident-runbook`, `grammarly-performance-tuning` | `grammarly-api-reliability` |
| `grammarly-security-basics`, `grammarly-reference-architecture` | `grammarly-data-safety-guardian` |
| `grammarly-enterprise-rbac` | `grammarly-license-governor` plus `grammarly-access-readiness` |
| `grammarly-cost-tuning`, `grammarly-prod-checklist`, `grammarly-webhooks-events` | Cut as standalone skills; verified safety and release checks moved into the five workflows. No public pricing/quota model or push-webhook contract is claimed. |

Because the old IDs had no alias mechanism, their removal is a deliberate major-version
change. No unsafe tombstone skill remains active or discoverable.

## Design and verification

- [`000-docs/000-INDEX.md`](000-docs/000-INDEX.md) — evidence and decision index
- [`000-docs/003-RL-RSRC-databricks-production-benchmark.md`](000-docs/003-RL-RSRC-databricks-production-benchmark.md) — production benchmark
- [`000-docs/004-AT-ADEC-grammarly-v2-cto-decision.md`](000-docs/004-AT-ADEC-grammarly-v2-cto-decision.md) — scope and safety decision
- `tests/test_grammarly_pack.py` — offline contract, boundary, and adversarial regression suite

## License

MIT
