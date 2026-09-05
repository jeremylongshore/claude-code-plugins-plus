# Grammarly v2 CTO decision

**Decision date:** 2026-09-04

**Status:** accepted for implementation; merge requires maintainer checkpoint.

## Decision

Replace the 24 v1 tutorial skills with five model-agnostic production operator skills
and release the change as `2.0.0`. Keep the `grammarly-pack` install identity. Ship a
complete machine-readable migration map and README table because the repository has no
skill-ID alias mechanism.

## Non-negotiable safety boundaries

1. Official current Grammarly documentation is authoritative for endpoints, scopes,
   fields, statuses, limits, and retention claims.
2. Unknown or conflicting contracts fail closed and are disclosed; no workaround is
   invented.
3. Offline is the default. The sole network helper is dry-run by default and requires
   exact content-digest confirmation.
4. Credentials enter only through environment variables. Raw content, bodies, tokens,
   presigned URLs, personal identifiers, and raw license IDs are excluded from receipts.
5. No automatic retry of job creation; idempotency is undocumented.
6. No synthetic scores, undocumented sandbox, webhook, pricing, quota, SDK, or account
   APIs.
7. License analysis is read-only and review-only; no DELETE automation ships.
8. No hooks, MCP server, dependency install, or Windows-only workflow is required.

## Compatibility disposition

The removed IDs are intentionally absent rather than retained as active tombstones:
unsafe instructions must not remain discoverable. `migration-map.json` provides the
human-readable migration reference; it is not a runtime alias or redirect mechanism.
This is a breaking change and therefore a major version.

## Approval boundary

Implementation may be committed, pushed, opened as a PR, and reviewed. It must not be
merged until required CI passes, security checks pass, automated reviewers finish, their
claims are independently checked, contributor credit is preserved where applicable,
and Jeremy receives the exact HEAD SHA and status summary.
