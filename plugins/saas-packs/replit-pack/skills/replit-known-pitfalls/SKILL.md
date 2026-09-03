---
name: replit-known-pitfalls
description: 'Audit a Replit App for persistence, Secrets, publishing, port, authentication, and deployment mistakes. Use when reviewing Replit code or diagnosing a Preview-to-production mismatch. Trigger with phrases like "replit mistakes", "replit anti-patterns", "replit pitfalls", or "replit code review".'
allowed-tools: Read, Grep, Bash(grep:*)
version: 1.13.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- replit
- audit
- anti-patterns
compatibility: Designed for Claude Code
---
# Replit Known Pitfalls

## Overview

Review a Replit App against current platform boundaries without changing deployment state. The audit distinguishes the editable Preview environment from the published app and treats model-generated code, production configuration, and public endpoints as separate trust boundaries.

## Prerequisites

- Read-only access to the project and its `.replit`, dependency manifests, server entry point, and authentication middleware.
- The intended deployment type and access policy: Public, Password protected, Workspace only, or Invite only.
- The expected production data stores, required Secret names, and public hostname. Do not request Secret values.
- Approval before changing Publishing settings, production data, DNS, or access controls.

## Instructions

1. Use `Read` to identify the run/build path, listening host and port, persistence layer, auth middleware, and health endpoint.
2. Use `Grep` or the count-only audit below to locate candidates. Treat matches as review leads, not proof of a vulnerability.
3. Compare Preview and published-app configuration explicitly. A successful Preview does not prove production Secrets, callbacks, data, or access settings are correct.
4. Classify each finding as confirmed, not applicable, or needs owner verification. Include file paths and remediation; never include credential values or raw customer data.
5. Stop before mutating a live app. Hand the owner a bounded change and a verification plan.

## Pitfall Reference

### Treating the published filesystem as durable

Published-app files reset when a new version is published. Store relational data in Replit Database and files or binary objects in App Storage. Do not claim that a successful local write proves durability.

### Assuming development Secrets are production-ready

Do not rely on automatic Secret carry-over. In Publishing, verify every required deployment Secret and environment variable by name, and add, link, or override it as the live pane requires; never display values. Never print the environment, paste Secret values into an issue, or expose them through a health route.

### Publishing a broken Preview

Publishing packages the current version; it does not repair a failing run command, dependency, or port. Make the main user journey pass in Preview first, then test it again at the stable published URL.

### Binding a server only to loopback

Published web servers must listen on `0.0.0.0`. If `.replit` contains explicit `[[ports]]`, ensure the intended `localPort` maps to `externalPort = 80`; explicit mappings disable automatic port detection.

### Trusting legacy identity headers

Do not invent authentication from raw `X-Replit-User-*` headers. Choose Replit Auth or Clerk Auth through the supported integration, verify the provider session in server middleware, and authorize access to each tenant-owned record. Use two accounts to test isolation.

### Defeating Autoscale with keep-alive traffic

Do not add synthetic pings to force an Autoscale app to stay warm. Choose Autoscale for variable traffic, Reserved VM for continuously available compute, Static only for client-only assets, and Scheduled for timetable-driven work. Record the cost and availability tradeoff.

### Publishing a backend as Static

Static deployments do not run API routes, server-side auth callbacks, database clients, or background processes. Select Autoscale or Reserved VM when the app requires a server.

### Logging raw exceptions or provider responses

Exception messages, request bodies, URLs, and headers can contain credentials or customer data. Log an event name, request identifier, error class, and allowlisted operational fields. Keep detailed evidence in an access-controlled incident system after review.

### Hard-coding time-sensitive limits

Plans, quotas, machine sizes, and prices change. Link the current usage or pricing page and capture the observed value and date in the deployment decision instead of embedding an unverified number in code.

## Examples

Run this count-only source audit from the project root. It reports counts, never matching lines or file contents.

```bash
set -euo pipefail

if candidate_secret_files="$(grep -rIlE \
  --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=.cache \
  --include='*.js' --include='*.jsx' --include='*.ts' --include='*.tsx' --include='*.py' \
  '(api[_-]?key|token|secret)[[:space:]]*[:=]' . 2>/dev/null)"; then
  :
else
  grep_status=$?
  [[ "$grep_status" -eq 1 ]] || { printf 'Source audit failed\n' >&2; exit 1; }
  candidate_secret_files=""
fi

if loopback_bind_files="$(grep -rIlE \
  --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=.cache \
  --include='*.js' --include='*.ts' --include='*.py' \
  '(listen|bind).*127\.0\.0\.1|(listen|bind).*localhost' . 2>/dev/null)"; then
  :
else
  grep_status=$?
  [[ "$grep_status" -eq 1 ]] || { printf 'Source audit failed\n' >&2; exit 1; }
  loopback_bind_files=""
fi

printf 'candidate_secret_assignments=%s\n' "$(printf '%s\n' "$candidate_secret_files" | grep -c . || true)"
printf 'loopback_bind_candidates=%s\n' "$(printf '%s\n' "$loopback_bind_files" | grep -c . || true)"
```

A production-readiness finding should look like this:

```text
Finding: server listens on 127.0.0.1 in src/server.ts
Impact: published app cannot receive routed traffic
Evidence: configuration path and line number only
Remediation: listen on 0.0.0.0 and verify the mapped/public port
Verification: Preview passes, then the published URL returns the expected status
```

## Output

Return a review table with finding, evidence location, impact, remediation, verification, owner, and disposition. Add a short list of assumptions that still require confirmation. Redact Secret values, session material, raw request bodies, customer content, and unrestricted logs.

## Error Handling

- If the project, deployment type, or production hostname is unavailable, mark the relevant checks `needs owner verification`; do not guess.
- If the audit finds a possible Secret, report only its file path and variable name, stop copying content, and recommend rotation if exposure is confirmed.
- If current Replit documentation conflicts with a saved template, prefer the current official page and flag the template as stale.
- If remediation would change billing, availability, access, DNS, or production data, stop for explicit approval.

## Resources

- [Troubleshoot publishing](https://docs.replit.com/build/troubleshooting)
- [Publishing overview](https://docs.replit.com/features/publishing/overview)
- [Deployment types](https://docs.replit.com/features/publishing/deployment-types)
- [Secrets](https://docs.replit.com/core-concepts/project-editor/app-setup/secrets)
- [Storage and Databases](https://docs.replit.com/learn/projects-and-artifacts/storage-and-databases)
- [Auth](https://docs.replit.com/learn/projects-and-artifacts/auth)
- [Security checklist](https://docs.replit.com/learn/security-checklist)
