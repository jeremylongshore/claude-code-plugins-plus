---
name: notion-security-basics
description: |
  Apply Notion API security best practices for integration tokens, OAuth2 flows,
  least-privilege capabilities, and page-level access control.
  Use when securing integration tokens, configuring OAuth2 for public integrations,
  rotating credentials, or auditing which pages an integration can access.
  Trigger with phrases like "notion security", "notion secrets",
  "secure notion", "notion API key security", "notion token rotation",
  "notion OAuth2", "notion permissions audit".
allowed-tools: Read, Write, Bash(npm:*), Bash(curl:*)
version: 1.38.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- productivity
- notion
compatibility: Designed for Claude Code
---
# Notion Security Basics

## Overview

Security fundamentals for the Notion API: integration token management, internal vs public integration models, principle of least privilege for capabilities, page-level access auditing, token rotation, OAuth2 flows for public integrations, and webhook verification. All examples use `@notionhq/client` v2.x and target the `2022-06-28` API version.

This SKILL.md gives you the workflow at a high level with the essential skeletons inline. Drill into the linked references for the full code:

- [Token storage, secret scanning, and access auditing](references/token-and-audit.md) — Step 1 + Step 2 in full
- [Token rotation, OAuth2, and webhook verification](references/oauth2-and-webhooks.md) — Step 3 in full
- [Worked examples](references/examples.md) — dual-integration `.env` + startup validation script

## Prerequisites

- Notion integration created at [notion.so/my-integrations](https://www.notion.so/my-integrations)
- Node.js 18+ with `@notionhq/client` installed (`npm install @notionhq/client`)
- Understanding of environment variables and `.env` file patterns
- For public integrations: OAuth2 client ID and secret from the integration dashboard

## Instructions

### Step 1: Secure Token Storage and `.env` Management

Integration tokens are secrets with the same sensitivity as database passwords. Notion tokens use the `ntn_` prefix (current) or `secret_` prefix (legacy). Both grant full access to every page shared with the integration. Two rules: never hardcode a token, and gitignore every `.env` variant BEFORE creating one.

Load from the environment and validate the token format before use:

```typescript
import { Client } from '@notionhq/client';

const token = process.env.NOTION_TOKEN;
if (!token) throw new Error('NOTION_TOKEN is required (see notion.so/my-integrations).');
if (!token.startsWith('ntn_') && !token.startsWith('secret_')) {
  throw new Error('NOTION_TOKEN has an unexpected format (expected ntn_ or legacy secret_).');
}

const notion = new Client({ auth: token });
```

Add a CI secret-scan step (`grep -rE "(ntn_|secret_)[a-zA-Z0-9]{30,}"`) so an accidentally committed token fails the build. Full `.gitignore` patterns, the `.env.example` template, and the complete GitHub Actions workflow are in [token storage, secret scanning, and access auditing](references/token-and-audit.md).

### Step 2: Least-Privilege Capabilities and Access Auditing

Configure integration capabilities at the [integration dashboard](https://www.notion.so/my-integrations). Each integration should request only the capabilities it actually uses — grant "Read content" to a dashboard, never "Insert/Update"; keep "Read user info (with email)" off unless you truly look up users by email.

Split responsibilities across separate integrations (a read-only `acme-reader`, a mutating `acme-writer`) so a leaked reader token cannot write. Audit access with an empty-query `notion.search()`, which returns every page and database the integration can reach:

```typescript
const response = await notion.search({ page_size: 100 });
// paginate on response.has_more / response.next_cursor to list all accessible objects
```

Remember the sharing hierarchy: sharing a parent cascades to children; sharing a child does not expose its parent; and the API returns `object_not_found` for both missing and unshared pages (intentional, to prevent leakage). The full capability matrix, the dual-client example, and the complete pagination-safe `auditIntegrationAccess()` function are in [token storage, secret scanning, and access auditing](references/token-and-audit.md).

### Step 3: Token Rotation, OAuth2, and Webhook Verification

**Rotation (internal integrations):** regenerating the secret at the dashboard *immediately* invalidates the old token, so update your secrets manager (AWS Secrets Manager / GCP Secret Manager / Vault) and restart services FIRST, then verify with `curl .../v1/users/me`. No separate revocation step is needed.

**OAuth2 (public integrations):** distribute to other workspaces via the authorization-code flow — redirect to `/v1/oauth/authorize` with a CSRF `state`, then exchange the code at `/v1/oauth/token` using HTTP Basic auth (`client_id:client_secret`) and store the returned per-workspace `access_token` encrypted (never in a cookie).

**Webhooks:** answer the `url_verification` challenge during setup, validate every payload's shape, respond `200` immediately, and process the event asynchronously.

Full multi-provider rotation commands, the complete Express OAuth2 handlers, and the hardened webhook endpoint are in [token rotation, OAuth2, and webhook verification](references/oauth2-and-webhooks.md).

## Output

After applying this skill:

- Integration tokens stored in environment variables, never in source code
- `.gitignore` configured to exclude all `.env` variants
- Git secret scanning workflow catches accidental token commits
- Integration capabilities set to the minimum required for each role
- Page access audited — you know exactly which pages the integration can reach
- Token rotation procedure documented with cloud provider commands
- OAuth2 flow implemented for public integrations (if applicable)
- Webhook endpoint validates payloads and responds asynchronously

## Error Handling

| Security Issue | Detection | Mitigation |
| ---------------- | ----------- | ------------ |
| Token committed to git | CI secret scan, `git log -p -S 'ntn_'` | Rotate immediately, rewrite git history with `git filter-repo` |
| Over-privileged integration | Capability audit at dashboard | Create new integration with minimal capabilities, migrate |
| Stale access to removed pages | Access audit script returns unexpected pages | Revoke page sharing, re-audit |
| Token never rotated | Track `created_time` of integration | Schedule quarterly rotation, automate with secrets manager |
| OAuth state mismatch | CSRF validation in callback | Reject the request, log the attempt |
| Webhook replay attacks | Duplicate event IDs | Track processed event IDs, skip duplicates |

## Examples

The essential skeleton — load a validated token and audit its reach — appears inline in Steps 1 and 2 above. For a complete, copy-ready setup see [worked examples](references/examples.md), which covers:

- A full `.env` for a dual-integration (reader/writer) architecture with OAuth2 vars
- A `validate-notion-config.ts` startup script that fails fast on missing env vars, an invalid/expired token (`unauthorized`), or an unshared database (`object_not_found`)

## Resources

- [Notion API Authorization](https://developers.notion.com/docs/authorization) — token types, OAuth2 flow, scopes
- [Create a Notion Integration](https://developers.notion.com/docs/create-a-notion-integration) — capabilities configuration
- [API Key Best Practices](https://developers.notion.com/docs/best-practices-for-handling-api-keys) — storage and rotation
- [@notionhq/client npm](https://www.npmjs.com/package/@notionhq/client) — official SDK documentation
- [Notion API Reference](https://developers.notion.com/reference/intro) — full endpoint reference

## Next Steps

For production deployment checklists, see `notion-prod-checklist`. For rate limit handling and retry strategies, see `notion-rate-limits`. For enterprise RBAC patterns with Notion, see `notion-enterprise-rbac`.
