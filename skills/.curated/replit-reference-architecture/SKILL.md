---
name: replit-reference-architecture
description: 'Design a production Replit App with explicit Preview/published boundaries, supported authentication, durable storage, safe configuration, health checks, and a workload-appropriate deployment type. Use when starting or reviewing a customer-facing Replit architecture. Trigger with phrases like "replit architecture", "replit production layout", or "replit best practices".'
allowed-tools: Read, Grep
version: 1.13.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- replit
- architecture
- reference
compatibility: Designed for Claude Code
---
# Replit Reference Architecture

## Overview

Design a Replit App around five boundaries: editable project versus published release, public edge versus server, authenticated user versus tenant data, ephemeral runtime versus durable storage, and development configuration versus production Secrets. Keep provider-specific details behind small adapters and confirm time-sensitive platform controls in current official documentation.

## Prerequisites

- A short workload profile: request-driven, continuously available, static, or scheduled.
- The app's public/private access policy, supported regions, cost owner, and availability target.
- A data classification and retention decision for relational records, files, logs, and backups.
- A chosen auth path: Replit Auth for Replit-account users or Clerk Auth for a branded tenant.
- Approval boundaries for publishing, production data changes, DNS, and access-control changes.

## Architecture

```text
Browser
  -> Replit published edge and access policy
    -> application server (Autoscale or Reserved VM)
      -> verified auth session -> tenant authorization
      -> Replit Database for structured records
      -> App Storage for files and binary objects
      -> allowlisted operational telemetry

Project Editor + Preview
  -> tests and release preparation
  -> explicit Publish/Republish action
  -> separate production configuration and verification
```

Static deployments stop at the published edge and client assets. They must not contain server-only credentials, database clients, auth callbacks, or background processes.

## Instructions

### Step 1 — Define the release boundary

Treat Preview as a development environment and the published URL as production. Changes in the Project Editor do not replace the live release until an explicit Publish or Republish. Record the source revision, migration state, production configuration names, and rollback/fix-forward decision for each release.

Use `Read` to inspect the existing architecture and configuration, and `Grep` to locate the relevant auth, storage, callback, health, and configuration-name call sites without exposing values.

### Step 2 — Keep configuration minimal

Use the current Project Editor and Publishing controls as authority. Keep `.replit` focused on commands and explicit ports only when automatic detection is insufficient:

```toml
entrypoint = "src/index.ts"
run = ["npm", "run", "dev"]

[deployment]
build = ["npm", "run", "build"]
run = ["npm", "start"]

[[ports]]
localPort = 3000
externalPort = 80
```

Do not hard-code a deployment target copied from an old template. Select Autoscale, Reserved VM, Static, or Scheduled in the current Publishing flow according to the workload and document the observed control.

### Step 3 — Separate configuration from Secret values

Validate names without logging values:

```typescript
const REQUIRED_CONFIGURATION = ["DATABASE_URL", "SESSION_SECRET"] as const;

export function assertProductionConfiguration(
  env: NodeJS.ProcessEnv,
): void {
  const missing = REQUIRED_CONFIGURATION.filter((name) => !env[name]);
  if (missing.length > 0) {
    console.error({
      event: "configuration_missing",
      missingCount: missing.length,
    });
    throw new Error("Required production configuration is missing");
  }
}
```

Do not rely on automatic Secret carry-over. In Publishing, verify every required deployment Secret and environment variable by name, and add, link, or override it as the live pane requires; never expose configuration values through client bundles, build logs, health responses, or debugging output.

### Step 4 — Put durable data in managed stores

Use Replit Database through a PostgreSQL-compatible client or ORM for structured records. Use App Storage for images, documents, exports, and other objects. Keep migrations explicit and forward/backward compatible across a rollout. Do not disable TLS certificate verification as a connection workaround.

Every tenant-owned query must derive the tenant/user identifier from a verified server-side session and include it in the authorization predicate. Storage object names are not an authorization boundary.

For example, scope every database query to the authenticated owner with a parameter, not a client-supplied identity:

```typescript
type VerifiedSession = { userId: string };
type Project = { id: string; name: string; ownerId: string };
type ProjectStore = {
  query<Row>(statement: string, parameters: readonly unknown[]): Promise<{ rows: Row[] }>;
};

async function listOwnedProjects(
  session: VerifiedSession | null,
  database: ProjectStore,
): Promise<Project[]> {
  if (!session) {
    throw new Error("authentication required");
  }

  const result = await database.query<Project>(
    "SELECT id, name, owner_id AS ownerId FROM projects WHERE owner_id = $1 ORDER BY id",
    [session.userId],
  );
  return result.rows;
}
```

### Step 5 — Use supported authentication

Choose Replit Auth or Clerk Auth through the supported integration. Verify sessions with the provider's server middleware, enforce authorization separately, and test with at least two users. For customer-facing branded products, evaluate Clerk's separate development and production environments; for Replit-account users, evaluate Replit Auth.

### Step 6 — Expose minimal operational endpoints

Keep public liveness cheap and non-sensitive:

```typescript
app.get("/healthz", (_request, response) => {
  response.status(200).json({ status: "ok" });
});
```

Send dependency health and diagnostic detail to authenticated monitoring, not the public response. Bind the server to `0.0.0.0` and ensure the configured local port matches any explicit `[[ports]]` mapping.

### Step 7 — Choose compute from the workload

| Workload | Candidate | Confirm before release |
|---|---|---|
| Variable request traffic | Autoscale | cold-start tolerance, maximum machines, cost |
| Continuous server or background connection | Reserved VM | capacity, availability, monthly cost |
| Client-only files | Static | no server routes, Secrets, or database access |
| Timetable-driven job | Scheduled | idempotency, overlap, retry and alert policy |

Avoid artificial keep-alive traffic. If latency requires continuously available compute, make that an explicit availability and billing decision.

## Examples

A customer-facing application might use Autoscale, Clerk Auth, Replit Database, and App Storage. Its release proof includes two-user tenant isolation, a reversible migration, a fast public `/healthz` response, and verification at the published URL.

An internal Replit-account tool might use Replit Auth and Workspace-only access. Authorization still belongs in server code; workspace access alone does not replace row-level ownership checks.

## Output

Produce an architecture decision record containing the workload, deployment candidate, trust boundaries, auth provider, data-store mapping, configuration names, public endpoints, monitoring signals, cost owner, release verification, and recovery path. Mark time-sensitive UI, plan, region, and quota facts as observed rather than universal.

## Error Handling

- If auth or storage ownership is unclear, stop the design at that boundary and request a decision.
- If a template conflicts with current Replit documentation, remove the stale assumption and cite the current page.
- If a health route would disclose dependency names, versions, paths, or Secret presence, replace it with coarse status and move details behind access control.
- If a deployment choice changes cost or availability, present the tradeoff and wait for owner approval.
- If a migration cannot safely coexist with the prior application version, require a maintenance or phased rollout plan before publishing.

## Resources

- [Publishing overview](https://docs.replit.com/features/publishing/overview)
- [Deployment types](https://docs.replit.com/features/publishing/deployment-types)
- [App configuration](https://docs.replit.com/features/project-setup/configuration)
- [Troubleshoot publishing](https://docs.replit.com/build/troubleshooting)
- [Storage and Databases](https://docs.replit.com/learn/projects-and-artifacts/storage-and-databases)
- [Auth](https://docs.replit.com/learn/projects-and-artifacts/auth)
- [Secrets](https://docs.replit.com/core-concepts/project-editor/app-setup/secrets)
- [Publishing costs](https://docs.replit.com/billing/deployment-pricing)
