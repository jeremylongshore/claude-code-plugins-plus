---
name: apify-debug-bundle
description: |
  Collect Apify debug evidence for support tickets and troubleshooting.
  Use when an Actor run has failed, is stuck, or produced empty output and
  you need to gather run metadata, logs, dataset samples, and environment
  info before opening a support ticket.
  Trigger with "apify debug", "apify support bundle", "collect apify logs",
  "apify diagnostic", "apify run failed why".
allowed-tools: Read, Bash(curl:*), Bash(npm:*), Bash(node:*), Bash(tar:*), Bash(apify:*),
  Grep
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
# Apify Debug Bundle

## Overview

Collect all diagnostic information needed to troubleshoot failed Actor runs and prepare Apify support tickets. Pulls run metadata, logs, dataset samples, and environment info into a single bundle so a support engineer (or you) can diagnose the failure without live access to your account.

## Prerequisites

- `apify-client` installed
- `APIFY_TOKEN` configured
- A failed or problematic run ID to investigate

## Authentication

All API calls authenticate with the `APIFY_TOKEN` as a Bearer header
(`Authorization: Bearer $APIFY_TOKEN`), and the SDK reads the same token from
`process.env.APIFY_TOKEN`. Get the token from the Apify Console under
**Settings → Integrations → Personal API tokens**. Never commit it — the bundle
script redacts any local `.env` before packaging, and the platform auto-redacts
secrets inside run logs.

## Instructions

The workflow has four steps. The skeleton below is enough to run it; each step's
full implementation lives in [implementation.md](references/implementation.md).

1. **Investigate the failed run** — pull run summary, dataset stats, and the log
   tail via the SDK. The core call:

   ```typescript
   const client = new ApifyClient({ token: process.env.APIFY_TOKEN });
   const run = await client.run(runId).get();
   const log = await client.run(runId).log().get();
   ```

2. **Create the debug bundle** — run `apify-debug-bundle.sh <RUN_ID>`. It
   collects environment info, run details, log, a 5-item dataset sample,
   key-value store keys, a redacted `.env`, and platform health, then packages
   everything into a timestamped `.tar.gz`. Full script in
   [implementation.md](references/implementation.md).

3. **Compare against a good run** (optional) — diff a successful and failed run
   field-by-field to spot the delta (`compareRuns(successId, failId)`).

4. **Live-tail a running Actor** (optional) — stream logs when the final log is
   not yet available.

For copy-pasteable code for every step, see
[implementation.md](references/implementation.md).

## Output

A single timestamped tarball, `apify-debug-YYYYMMDD-HHMMSS.tar.gz`, containing:

| File | Contents |
|------|----------|
| `environment.txt` | Node/npm versions, installed Apify packages, CLI version |
| `run-details.json` | Run status, options, stats, usage, cost |
| `run-log.txt` | Full run log (secrets auto-redacted by the platform) |
| `dataset-sample.json` | First 5 dataset items |
| `kv-store-keys.json` | Key-value store key listing |
| `env-redacted.txt` | Local `.env` with all values redacted |
| `platform-health.json` | Apify platform health snapshot |

Attach the tarball directly to an Apify support ticket.

## Sensitive Data Handling

**Always redact before sharing:**

- API tokens (`apify_api_*`)
- Proxy passwords
- PII (emails, names, IPs)
- Custom environment variables

**Safe to include:**

- Run IDs, Actor IDs, dataset IDs
- Error messages and stack traces
- Run configuration (memory, timeout)
- Platform health status

## Escalation Path

1. Check run log for stack trace
2. Compare with a successful run
3. Check [Apify Status](https://status.apify.com) for outages
4. Create debug bundle
5. Submit to [Apify Support](https://console.apify.com/support) with bundle attached

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `Run not found` | Invalid run ID or expired | Unnamed runs expire after 7 days |
| `Log unavailable` | Run still in progress | Wait for completion or stream live |
| Empty dataset | Actor produced no output | Check `failedRequestHandler` in code |
| High CU usage | Memory too high or slow execution | Reduce memory, optimize code |

## Examples

Four worked scenarios — a plain `FAILED` run, an "it worked yesterday"
regression diff, an empty-dataset investigation, and live-tailing a hung run —
are in [examples.md](references/examples.md). The quickest path:

```bash
export APIFY_TOKEN="apify_api_..."
./apify-debug-bundle.sh abc123DEF          # → apify-debug-20260717-142530.tar.gz
tar -xzf apify-debug-*.tar.gz && tail -40 apify-debug-*/run-log.txt
```

See [examples.md](references/examples.md) for the full walkthroughs, including
reading the comparison output and interpreting a live tail.

## Resources

- [Full implementation walkthrough](references/implementation.md)
- [Worked examples](references/examples.md)
- [Actor Run API](https://docs.apify.com/api/v2/actor-run-get)
- [Run Log API](https://docs.apify.com/api/v2)
- [Apify Support Portal](https://console.apify.com/support)

## Next Steps

For rate limit issues, see the `apify-rate-limits` skill.
