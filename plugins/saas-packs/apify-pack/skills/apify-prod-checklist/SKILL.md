---
name: apify-prod-checklist
description: |
  Production readiness checklist for Apify Actor deployments.
  Use when deploying an Actor to production, preparing for launch, or
  validating Actor configuration, scheduling, monitoring, and rollback
  before going live.
  Trigger with "apify production", "deploy actor to prod", "apify go-live",
  "apify launch checklist", "actor production ready".
allowed-tools: Read, Bash(apify:*), Bash(curl:*), Bash(npm:*)
version: 1.5.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- scraping
- automation
- apify
compatibility: Designed for Claude Code
---
# Apify Production Checklist

## Overview

Complete checklist for deploying Actors to the Apify platform and integrating them into production applications. Covers Actor configuration, scheduling, monitoring, alerting, and rollback. Work top to bottom: clear the pre-deployment gates, then run the six deploy steps, then wire the alert conditions.

## Prerequisites

- Actor tested locally with `apify run`
- `apify login` configured with production token
- Familiarity with `apify-core-workflow-a` and `apify-deploy-integration`

## Pre-Deployment Checklist

### Actor Configuration

- [ ] `.actor/actor.json` has correct `name`, `title`, `description`
- [ ] `INPUT_SCHEMA.json` validates all required inputs
- [ ] `Dockerfile` uses pinned base image version (`apify/actor-node:20`, not `latest`)
- [ ] `package-lock.json` committed (deterministic installs)
- [ ] Memory set appropriately (start at 1024MB, tune after profiling)
- [ ] Timeout set with buffer (2x expected runtime)

### Code Quality

- [ ] `Actor.main()` wraps entry point (handles init/exit/errors)
- [ ] `failedRequestHandler` logs failures without crashing Actor
- [ ] Input validation at Actor start (`if (!input?.startUrls) throw ...`)
- [ ] No hardcoded URLs, credentials, or magic numbers
- [ ] Proxy configured for target sites that block datacenter IPs
- [ ] `maxRequestsPerCrawl` set to prevent runaway costs

### Data Output

- [ ] Dataset schema documented (consistent field names)
- [ ] `SUMMARY` key-value store record saved with run stats
- [ ] Large payloads chunked (9MB dataset push limit)
- [ ] PII sanitized before storage

## Instructions

Read the Actor's `.actor/actor.json`, `INPUT_SCHEMA.json`, and `Dockerfile` first to confirm the pre-deployment gates above, then run the six deploy steps. Each step's full command and code block lives in [references/implementation.md](references/implementation.md); the skeleton is below.

1. **Deploy Actor** — `apify push`, then `apify builds ls` to confirm the build, then `apify actors call` with a small production-like input to smoke-test on-platform.
2. **Configure Scheduling** — create a cron schedule with `client.schedules().create({...})` (or Apify Console: Actors > Your Actor > Schedules). Set `cronExpression`, `runInput`, and `runOptions` (memory/timeout).
3. **Set Up Webhooks** — `client.webhooks().create({...})` on `ACTOR.RUN.SUCCEEDED`/`FAILED`/`TIMED_OUT` with a `payloadTemplate` posting runId, status, and datasetId to your server.
4. **Monitor Runs** — a `checkActorHealth(actorId, lookbackHours)` helper lists recent runs and reports success rate, failures, timeouts, and total cost.
5. **Implement Rollback** — `apify builds ls`, then repoint the Actor at a prior build via the `POST /v2/acts/ACTOR_ID?build=N` API, or redeploy from a git tag.
6. **Cost Guard** — `runWithCostGuard(actorId, input, maxCostUsd)` polls `usageTotalUsd` every 30s and aborts the run if it exceeds budget.

The first deploy step in full:

```bash
# Build and push to Apify platform
apify push

# Verify the build succeeded
apify builds ls
```

## Output

Working through this skill produces a production-ready Actor with:

- A pushed, verified build (`apify builds ls` shows a `SUCCEEDED` build).
- A live cron **schedule** and a completion **webhook** firing on success/failure/timeout.
- A repeatable **health check** printing success rate, failure/timeout counts, and 24h cost.
- A tested **rollback** path (build repoint or git-tag redeploy).
- A **cost guard** that aborts runs exceeding budget.

Health-check output looks like:

```text
Actor: username/product-scraper
Last 24h: 3 runs, 66.7% success
Failed: 1, Timed out: 0
Total cost: $0.4213
```

## Production Alert Conditions

| Alert | Condition | Severity |
|-------|-----------|----------|
| Run failed | `status === 'FAILED'` | P1 |
| Run timed out | `status === 'TIMED-OUT'` | P2 |
| Low yield | Dataset items < expected threshold | P2 |
| High cost | `usageTotalUsd > budget` | P2 |
| Consecutive failures | 3+ failures in a row | P1 |
| No runs in window | Schedule didn't trigger | P1 |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Build fails on platform | Local deps differ | Commit `package-lock.json` |
| Schedule not firing | Cron syntax error | Validate at crontab.guru |
| Webhook not received | URL not reachable | Use ngrok for testing; check HTTPS |
| Memory exceeded | Workload too large | Increase memory or reduce concurrency |
| Unexpected cost spike | No `maxRequestsPerCrawl` | Always set an upper bound |

## Examples

Four worked examples — a first production deploy, health-check output, a cost guard aborting a runaway run, and a build rollback — are in [references/examples.md](references/examples.md). A first production deploy in brief:

```bash
# Smoke-test on-platform with a tiny input before scheduling
apify actors call username/product-scraper \
  --input='{"startUrls":[{"url":"https://target.com"}],"maxItems":10}'
```

Then create the daily schedule and completion webhook (implementation.md Steps 2–3).

## Resources

- [Full deploy walkthrough (Steps 1–6)](references/implementation.md)
- [Worked examples](references/examples.md)
- [Actor Deployment Guide](https://docs.apify.com/platform/actors/development/deployment)
- [Schedules Documentation](https://docs.apify.com/platform/schedules)
- [Webhook Event Types](https://docs.apify.com/platform/integrations/webhooks/events)
- [Usage & Billing](https://docs.apify.com/platform/actors/running/usage-and-resources)

## Next Steps

Once production is stable, plan version upgrades with the `apify-upgrade-migration` skill: it covers bumping the Actor base image, migrating `INPUT_SCHEMA.json` fields without breaking existing schedules, and re-running this checklist against the new build before repointing traffic.
