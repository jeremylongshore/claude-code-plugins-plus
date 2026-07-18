---
name: notion-policy-guardrails
description: |
  Use when you need to govern Notion integrations at scale — set integration
  naming standards, enforce page sharing policies, standardize property naming
  and database schemas, and run access audits that scan which bots can reach
  which pages. Trigger with phrases like "notion governance", "notion policy",
  "notion naming convention", "notion access audit", "notion schema standard".
allowed-tools: Read, Write, Edit, Bash(npx:*), Bash(node:*)
version: 1.38.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- productivity
- notion
compatibility: Designed for Claude Code
---
# Notion Policy & Guardrails

## Overview

Governance framework for Notion integrations at scale. Covers integration
naming standards, page sharing policy enforcement, property naming conventions,
database schema validation, and access audit scripts. Uses `Client` from
`@notionhq/client` for programmatic enforcement.

## Prerequisites

- `@notionhq/client` v2.x installed (`npm install @notionhq/client`)
- Python: `notion-client` installed (`pip install notion-client`)
- `NOTION_TOKEN` environment variable set (admin-level integration recommended for audits)
- CI/CD pipeline (GitHub Actions examples provided)

## Authentication

All scripts authenticate with a Notion **internal integration token** read from
the `NOTION_TOKEN` environment variable — never hardcode it. Create the token at
notion.so/my-integrations, share the target pages/databases with the integration,
and inject the token via CI secrets (e.g. `secrets.NOTION_AUDIT_TOKEN`). Audit
scripts want a broadly-shared admin integration; runtime bots want the narrowest
sharing scope that works. Token rotation is tracked in Step 1 (max 90 days).

## Instructions

The workflow has three stages. Each stage's full enforcement code (TypeScript +
Python) lives in [references/implementation.md](references/implementation.md) —
the skeletons below show the shape; drill into the reference for the complete
functions.

### Step 1: Integration Naming Standards and Token Management

Establish a `{team}-{env}-{purpose}` naming convention (e.g. `eng-prod-sync`) so
teams can identify which bot accessed what, validate it at startup, and track
token rotation (max 90 days). Core check:

```typescript
// Must match: /^[a-z]+-[a-z]+-[a-z]+$/  →  eng-prod-sync
function validateIntegrationName(name: string): string[] { /* ... */ }
```

Full `IntegrationConfig`, startup validation, and `checkTokenExpiry` registry:
[references/implementation.md](references/implementation.md) § Step 1.

### Step 2: Page Sharing Policies and Property Naming Conventions

Standardize property names across databases (PascalCase titles, `Date`/`At`
suffixes on dates, plural multi-selects, a banned-name list) and audit which
pages are shared publicly. Core check:

```typescript
async function auditDatabaseSchema(notion, databaseId):
  Promise<{ violations: string[]; recommendations: string[] }> { /* ... */ }
```

Full `PROPERTY_NAMING_RULES`, `auditPageAccess`, and the Python port:
[references/implementation.md](references/implementation.md) § Step 2.

### Step 3: Access Audit Scripts and Database Schema Standards

Run a paginated, rate-limited workspace audit of everything the integration can
reach, and gate schema drift in CI. Core check:

```typescript
async function workspaceAccessAudit(notion: Client): Promise<void> { /* ... */ }
// Flags integrations with access to >1000 items; enumerates every database.
```

Full `validateSchemaInCI`, the GitHub Actions workflow (weekly cron + token
scan), and the Python port: [references/implementation.md](references/implementation.md) § Step 3.

## Output

- Integration naming standards validated at startup
- Token rotation tracking with expiry warnings
- Property naming conventions audited against database schemas
- Access audit showing all content visible to the integration
- CI workflow enforcing schema standards and secret scanning
- Violation report with actionable recommendations

## Error Handling

| Issue | Cause | Solution |
| ------- | ------- | ---------- |
| Audit shows too many pages | Integration shared at workspace level | Narrow sharing to specific pages/databases |
| Schema validation fails | Property renamed in Notion UI | Update schema config to match |
| Token scan false positive | Test fixtures contain example tokens | Add `--exclude` for test directories |
| `object_not_found` during audit | Page unshared since last audit | Expected — log and continue |
| Naming convention too strict | Legacy integrations don't match | Add exceptions list with migration deadline |

## Examples

A one-line CI secret scan and the `.env`-not-committed guard:

```bash
grep -rn "ntn_\|secret_" --include="*.ts" --include="*.js" src/ && echo "FAIL: Token found" || echo "PASS: No tokens"
git ls-files | grep -E "^\.env" && echo "FAIL: .env committed" || echo "PASS"
```

For the full `SCHEMA_REGISTRY` (per-database required-property maps that feed
CI validation) and more, see [references/examples.md](references/examples.md).

## Resources

- [Notion Integration Best Practices](https://developers.notion.com/docs/best-practices-for-handling-api-keys)
- [Notion Authorization Guide](https://developers.notion.com/docs/authorization)
- [ESLint Custom Rules](https://eslint.org/docs/latest/extend/plugins)
- [Pre-commit Framework](https://pre-commit.com/)

## Next Steps

For architecture blueprints, see `notion-architecture-variants`.
For common mistakes to avoid, see `notion-known-pitfalls`.
