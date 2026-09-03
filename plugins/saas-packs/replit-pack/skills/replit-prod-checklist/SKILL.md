---
name: replit-prod-checklist
description: 'Prepare, publish, and verify a production Replit App with explicit access, Secrets, auth, storage, health, monitoring, cost, and recovery checks. Use when going live or republishing an Autoscale, Reserved VM, Static, or Scheduled workload. Trigger with phrases like "replit production", "publish replit", "replit launch checklist", or "replit prod ready".'
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.13.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- replit
- deployment
- production
compatibility: Designed for Claude Code
---
# Replit Production Checklist

## Overview

Build a release receipt before publishing and verify the stable public URL afterward. The checklist avoids assuming that Preview state, development Secrets, local files, or a saved deployment template automatically become production state.

## Prerequisites

- Publishing access plus an owner-approved access policy, deployment type, region, machine limits, and cost boundary.
- A source revision that passes the main user journey in Preview.
- Named production configuration variables, auth environment, data stores, migrations, and recovery owner.
- The exact generated `replit.app` origin. Review custom domains separately.
- A tested rollback or fix-forward plan that does not assume application recovery reverses database changes.

## Instructions

### Step 1 — Review the release boundary

Use `Read` to inspect the declared configuration and release inputs, and `Grep` to locate relevant auth, storage, callback, health, and Secret-name call sites without printing values.

- [ ] Record source revision, build/run commands, migration version, deployment type, and release owner.
- [ ] Confirm changes were tested in Preview and identify what must be retested at the published URL.
- [ ] Remove private test data, local-only assumptions, and unneeded generated files from the release.
- [ ] Confirm Publish/Republish is the only action that promotes the new version.

### Step 2 — Confirm deployment and ports

- [ ] Select Autoscale for variable request traffic, Reserved VM for continuously available compute, Static only for client-only assets, or Scheduled for timetable-driven work.
- [ ] Record current region, machine power, maximum machine count where applicable, and cost owner.
- [ ] Ensure a web server stays running and listens on `0.0.0.0`.
- [ ] If `.replit` declares `[[ports]]`, map the intended `localPort` to `externalPort = 80`.
- [ ] Do not copy an old `deploymentTarget` value into a new app without confirming the current UI/documentation.

### Step 3 — Verify production Secrets and access

- [ ] Review security in the Publish dialog.
- [ ] Select Public, Password protected, Workspace only, or Invite only intentionally.
- [ ] Do not rely on automatic Secret carry-over. In Publishing, verify every required deployment Secret and environment variable by name, and add, link, or override it as the live pane requires; never display values.
- [ ] Link account-level Secrets explicitly when used.
- [ ] Confirm no server credential is bundled into browser JavaScript, Static assets, logs, or health output.

### Step 4 — Verify auth and tenant isolation

- [ ] Confirm Replit Auth or Clerk Auth is provisioned for the intended environment.
- [ ] Verify sessions server-side and enforce authorization separately.
- [ ] Test with two users; each must see only records and objects they own.
- [ ] Confirm production callback URLs, cookie attributes, sign-out, and unauthenticated behavior.

### Step 5 — Verify durable data

- [ ] Use Replit Database for structured relational data and App Storage for files/objects.
- [ ] Confirm the published app does not rely on local files surviving a release.
- [ ] Apply a reviewed, reversible or backward-compatible migration plan.
- [ ] Confirm backups and restore evidence through the data-store-specific process.
- [ ] Never disable TLS certificate verification as a connectivity shortcut.

### Step 6 — Expose minimal health and errors

The public liveness response should be fast and coarse:

```typescript
app.get("/healthz", (_request, response) => {
  response.status(200).json({ status: "ok" });
});

app.use((error: Error, request: Request, response: Response, _next: NextFunction) => {
  const requestId = crypto.randomUUID();
  console.error({
    event: "request_failed",
    requestId,
    errorClass: error.name,
  });
  response.status(500).json({ error: "Internal server error", requestId });
});
```

- [ ] Keep database topology, versions, paths, Secret state, stack traces, and raw errors out of public responses.
- [ ] Keep the published root response within Replit's current promotion timing requirement; keep `/healthz` fast and coarse for post-publish verification.
- [ ] Route detailed dependency checks to authenticated monitoring.

### Step 7 — Publish and verify

- [ ] Publish with the approved domain and access settings.
- [ ] Wait for provisioning, build, security checks, and promotion to complete.
- [ ] Test the main user journey at the published URL, not only Preview.
- [ ] Verify authentication, tenant isolation, writes, reads, uploads, callbacks, and sign-out where applicable.
- [ ] Open Monitoring and inspect requests, HTTP status, duration, CPU, and memory.
- [ ] Record the release result and stabilization window before closing the change.

### Step 8 — Preserve recovery

- [ ] Record the last verified release and current migration state.
- [ ] Define the trigger and owner for rollback or fix-forward.
- [ ] Verify recovery at the public URL after execution.
- [ ] Keep database recovery separate from application release recovery.

## Examples

Run this body-free canary only against the exact Replit-owned production origin:

```bash
set -euo pipefail
: "${REPLIT_DEPLOY_URL:?Set the exact https://<app>.replit.app origin}"

if [[ ! "$REPLIT_DEPLOY_URL" =~ ^https://[a-z0-9]([a-z0-9-]*[a-z0-9])?\.replit\.app$ ]]; then
  printf 'Refusing unapproved deployment origin\n' >&2
  exit 64
fi

probe="$(curl --silent --show-error --output /dev/null \
  --write-out '%{http_code} %{time_total}' --connect-timeout 5 --max-time 10 \
  --proto '=https' "$REPLIT_DEPLOY_URL/healthz")" || {
  printf 'Published app probe failed\n' >&2
  exit 1
}
read -r status_code duration_seconds <<<"$probe"
[[ "$status_code" =~ ^2[0-9]{2}$ && "$duration_seconds" =~ ^[0-9]+([.][0-9]+)?$ ]] || {
  printf 'Published app is not healthy\n' >&2
  exit 1
}
printf '{"http_status":%s,"duration_seconds":%s}\n' "$status_code" "$duration_seconds"
```

A release receipt should identify the source revision, deployment type, access policy, production configuration names, migration, public checks, owner, and recovery path. Store links to restricted evidence instead of raw logs.

## Output

Return a pass/fail/blocked checklist plus an immutable release receipt. Every blocked item must name the missing evidence or owner decision. Do not declare production-ready while access, auth isolation, data durability, public verification, monitoring, or recovery remains unproven.

## Error Handling

- If Preview fails, stop before publishing and diagnose the application first.
- If production Secrets or access settings are uncertain, block the release rather than printing or guessing them.
- If the published health check is non-2xx or malformed, preserve the failed release evidence and use the approved recovery path.
- If monitoring shows elevated errors or resource saturation, stop promotion and involve the cost/availability owner before resizing.
- If a migration failure may have changed data, freeze further migrations and follow the database recovery plan.

## Resources

- [Publishing overview](https://docs.replit.com/features/publishing/overview)
- [Deployment types](https://docs.replit.com/features/publishing/deployment-types)
- [App configuration](https://docs.replit.com/features/project-setup/configuration)
- [Custom domains](https://docs.replit.com/features/publishing/custom-domains)
- [Security checklist](https://docs.replit.com/learn/security-checklist)
- [Troubleshoot publishing](https://docs.replit.com/build/troubleshooting)
- [Secrets](https://docs.replit.com/core-concepts/project-editor/app-setup/secrets)
- [Storage and Databases](https://docs.replit.com/learn/projects-and-artifacts/storage-and-databases)
- [Auth](https://docs.replit.com/learn/projects-and-artifacts/auth)
- [Version control and checkpoints](https://docs.replit.com/learn/projects-and-artifacts/version-control)
- [Publishing costs](https://docs.replit.com/billing/deployment-pricing)
