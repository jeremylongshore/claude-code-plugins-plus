---
name: replit-common-errors
description: 'Diagnose Replit Preview and publishing failures involving commands, dependencies, ports, production Secrets, storage, authentication, or deployment type. Use when an app works in one Replit environment but fails in another. Trigger with phrases like "replit error", "replit not working", "replit deploy failed", or "debug replit".'
allowed-tools: Read, Grep
version: 1.13.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- replit
- debugging
- errors
compatibility: Designed for Claude Code
---
# Replit Common Errors

## Overview

Diagnose Replit failures by locating the first boundary that fails: local code, Preview, publishing, or the stable public URL. Preserve production state while investigating and use current Replit documentation instead of legacy plan names, fixed quotas, or old deployment controls.

## Prerequisites

- The exact failing URL class: Preview on `replit.dev` or published app on `replit.app`/a custom domain.
- The failing action, observed HTTP status or UI error, first-seen time, and last known-good release.
- Read-only access to the project, Publishing logs, and monitoring. Request Secret names and presence, never values.
- The expected deployment type and access policy.

## Instructions

1. Reproduce the smallest failing user action without changing configuration.
2. If Preview fails, inspect the run command, dependency installation, server logs, and port binding before opening Publishing.
3. If Preview works but publishing fails, inspect the Publishing build/run command, production Secrets, long-running process behavior, and health-check timing.
4. If publishing succeeds but the public URL fails, compare production callbacks, database configuration, CORS/API allowlists, persisted storage, access policy, and browser behavior.
5. Use `Read` for configuration and `Grep` for relevant call sites. Do not dump the environment, raw request bodies, session cookies, or entire logs.
6. Change one bounded cause, republish only with approval, and verify both the original failure and a core user journey.

## Error Reference

### Preview is blank or unreachable

- Confirm the process stays running.
- Bind the HTTP server to `0.0.0.0`, not loopback.
- If `.replit` declares `[[ports]]`, map the server's `localPort` to `externalPort = 80`.
- Remove stale explicit mappings only after confirming automatic port detection is intended.

### Publishing build fails

- Compare the configured build command with the command that succeeds in Preview.
- Confirm lockfiles and production dependencies are committed.
- Remove unrelated generated artifacts or oversized files rather than skipping build validation.
- Do not guess at a timeout value; use the failure stage and logs to reduce actual work.

### Published process repeatedly restarts

- Ensure the run command starts a long-running server rather than a one-shot script.
- Validate required configuration at startup without printing values.
- Treat out-of-memory and crash-loop symptoms separately; changing machine size can affect cost and may only mask a leak.

### Health check fails during promotion

Replit checks the app before marking a release live. Keep the published root response fast and bounded; current troubleshooting guidance says the homepage must respond within five seconds. A public health response should reveal only coarse status, not database topology, stack traces, versions, filesystem paths, or Secret presence.

### Production Secret is missing

Do not rely on automatic Secret carry-over. In Publishing, verify every required deployment Secret and environment variable by name, and add, link, or override it as the live pane requires; never display values. Do not troubleshoot by printing `process.env` or `printenv`.

### Database works in Preview but not production

- Confirm `DATABASE_URL` exists in the published environment without displaying it.
- Confirm the production database and migration state are intentional.
- Use the PostgreSQL client or ORM defaults required by the current provider; never disable TLS certificate verification as a generic fix.
- Bound pool size and connection timeouts to the deployed machine and workload.

### Uploaded files disappear after republishing

The published filesystem is not durable across releases. Move structured data to Replit Database and files to App Storage. Do not store user uploads, backups, or generated reports only on the local filesystem.

### Login succeeds in Preview but fails publicly

Verify the selected Replit Auth or Clerk integration, production environment, callback URL, cookie settings, and access policy. Do not substitute raw request headers for provider session verification. Test with two users and confirm each sees only owned records.

### Static deployment cannot reach an API

Static is for client-only files. An app with server routes, auth callbacks, database access, or background logic needs Autoscale or Reserved VM. Never move a Secret into client code to make Static appear to work.

### Public URL still shows the previous release

Project Editor changes do not automatically replace the live deployment. Confirm which version was published, republish deliberately, then open the public URL and verify the changed behavior.

## Examples

For a Preview-only failure:

```text
Observed: Run starts, Preview remains blank
Check: process lifetime -> bind host -> .replit port mapping -> application error
Evidence: command name, status, and file location only
Stop condition: first confirmed boundary failure
```

For a production-only authentication failure:

```text
Observed: Preview sign-in succeeds; public callback returns 401
Check: provider production environment, published callback URL, cookie policy, access setting
Forbidden shortcut: trusting legacy identity headers or moving credentials client-side
Verification: two-user isolation test at the published URL
```

## Output

Return the failing boundary, the smallest reproducible symptom, evidence locations, ranked hypotheses, one next safe check, and the verification/rollback plan. Separate confirmed facts from assumptions and redact user data, credentials, URLs containing tokens, and raw provider responses.

## Error Handling

- If the issue cannot be reproduced, preserve timestamps and monitoring evidence and state what additional signal is required.
- If Replit status reports a platform incident, avoid speculative configuration changes; communicate impact and monitor recovery.
- If logs contain possible credentials or customer content, stop copying them and use an approved redaction/review path.
- If the fix changes cost, access, DNS, production data, or deployment type, obtain explicit approval.
- If official documentation and the UI disagree, capture the page/date and ask the owner to confirm the live control rather than inventing a command.

## Resources

- [Troubleshoot publishing](https://docs.replit.com/build/troubleshooting)
- [Publishing overview](https://docs.replit.com/features/publishing/overview)
- [Deployment types](https://docs.replit.com/features/publishing/deployment-types)
- [Secrets](https://docs.replit.com/core-concepts/project-editor/app-setup/secrets)
- [Storage and Databases](https://docs.replit.com/learn/projects-and-artifacts/storage-and-databases)
- [Auth](https://docs.replit.com/learn/projects-and-artifacts/auth)
- [Replit Status](https://status.replit.com)
