---
name: notion-ci-integration
description: 'Integrate the Notion API into CI/CD pipelines for automated documentation
  sync,

  deploy tracking, and configuration reads. Use when setting up GitHub Actions

  workflows that push release notes to Notion, update database entries on deploy,

  create incident pages from CI, or read feature flags from Notion databases.

  Trigger with phrases like "notion CI", "notion GitHub Actions", "notion deploy sync",

  "notion release notes automation", "notion CI pipeline".

  '
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(npm:*), Bash(npx:*), Bash(python3:*)
version: 1.38.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- productivity
- notion
- ci-cd
- devops
compatibility: Designed for Claude Code
---
# Notion CI Integration

## Overview

Integrate the Notion API into CI/CD pipelines for automated documentation sync, deploy tracking, and configuration reads. GitHub Actions workflows push release notes to Notion pages, upsert deploy entries in databases, create incident pages, and read feature flags — all with rate-limit handling, and each concern in its own reference file for copy-ready code.

## Prerequisites

- GitHub repository with Actions enabled
- Notion internal integration token (create at `https://www.notion.so/my-integrations`)
- Target Notion pages/databases shared with the integration (click "..." > "Connections" > add the integration)
- `NOTION_TOKEN` stored as a GitHub Actions secret
- Node.js 18+ or Python 3.9+ in the CI environment

## Authentication

Every request authenticates with an internal integration token passed as a bearer
credential. The Notion SDKs read it from the `NOTION_TOKEN` environment variable
(`new Client({ auth: process.env.NOTION_TOKEN })` in Node, `Client(auth=token)` in
Python). Store it as a repository secret and inject it per job — never hardcode it
(`gh secret set NOTION_TOKEN`). A token only reaches pages and databases explicitly
shared with the integration (page menu > "Connections" > add integration); an unshared
target returns `404 Object not found`, not `401` — see [Error Handling](#error-handling).

## Instructions

The integration is three composable pieces — read each summary for its shape, then open the linked reference for complete, copy-ready code.

### Step 1: Workflow for documentation sync

Add a workflow that reacts to `release: published` and pushes to `main`. It runs three
jobs — create a release-notes page, sync the `CHANGELOG.md` page, and update the deploy
tracker — each injecting `NOTION_TOKEN` and the relevant database ID as `env`:

```yaml
# .github/workflows/notion-docs-sync.yml
on:
  release: { types: [published] }
env:
  NOTION_TOKEN: ${{ secrets.NOTION_TOKEN }}
jobs:
  sync-release-notes:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4      # + npm ci (see reference)
      - run: node scripts/notion-release-sync.js
        env:
          NOTION_RELEASES_DB: ${{ secrets.NOTION_RELEASES_DB }}
          RELEASE_TAG: ${{ github.event.release.tag_name }}
```

See [full workflow YAML](references/workflow-setup.md) for all three jobs, the
changelog push trigger, and the `needs:`-gated deploy-status job.

### Step 2: CI scripts for Notion operations

Back the workflow with small scripts. The release-notes script creates a database page
and appends the body as blocks in chunks of 100 (Notion's per-request limit) with a
350ms delay between batches:

```typescript
// scripts/notion-release-sync.js — skeleton
const notion = new Client({ auth: process.env.NOTION_TOKEN });
const page = await notion.pages.create({
  parent: { database_id: process.env.NOTION_RELEASES_DB },
  properties: { Name: { title: [{ text: { content: `Release ${tag}` } }] } },
});
for (let i = 0; i < blocks.length; i += 100) {
  await notion.blocks.children.append({ block_id: page.id, children: blocks.slice(i, i + 100) });
  if (i + 100 < blocks.length) await sleep(350);   // stay under 3 req/sec
}
```

See [CI scripts](references/ci-scripts.md) for the complete release-notes and
deploy-status upsert scripts (Node.js) plus a Python batch updater with `--dry-run`
and `retry-after` handling.

### Step 3: Reading configuration from Notion in CI

Treat a Notion database as a feature-flag store that non-engineers can edit. Query it
filtered by environment, extract `Key`/`Value` pairs, and write `notion-config.json`
for downstream CI steps to read:

```typescript
// scripts/notion-read-config.js — skeleton
const response = await notion.databases.query({
  database_id: process.env.NOTION_CONFIG_DB,
  filter: { property: 'Environment', select: { equals: process.env.DEPLOY_ENV } },
});
writeFileSync('notion-config.json', JSON.stringify(config, null, 2));
```

See [config reads](references/config-reads.md) for the full extraction script and the
GitHub Actions steps that load and consume the flags.

## Output

- GitHub Actions workflow that syncs release notes to a Notion database on every release
- Deploy tracker that updates database entries with status "Deployed", version tag, commit SHA, and timestamp
- Python batch update script for bulk status changes in CI (with `--dry-run` safety)
- Config reader that pulls feature flags from Notion databases into the CI environment
- Every script handles rate limits via sequential operations and 350ms delays between requests

## Error Handling

| Issue | Cause | Solution |
| ------- | ------- | ---------- |
| `401 Unauthorized` | Invalid or expired `NOTION_TOKEN` | Regenerate token at notion.so/my-integrations, update `gh secret set NOTION_TOKEN` |
| `404 Object not found` | Database/page not shared with integration | Open page in Notion > "..." > "Connections" > add integration |
| `429 Rate limited` | Exceeded 3 requests/second | Add `time.sleep(0.34)` between sequential calls; use `retry-after` header |
| `400 Validation error` | Property name mismatch or wrong type | Verify property names exactly match database schema (case-sensitive) |
| `Secret not found` in CI | `NOTION_TOKEN` not configured | Run `gh secret set NOTION_TOKEN` and paste the integration token |
| Timeout in CI | Large batch operations | Set `timeout-minutes: 10` on the job; process in chunks of 100 |
| `ECONNRESET` in CI | Transient network failure | SDK has built-in retry (2 retries with exponential backoff by default) |

## Examples

### Incident Report Creator (GitHub Actions)

Create structured incident pages from CI using `workflow_dispatch`. Dispatched manually or via `gh workflow run` with severity, title, and description inputs. Creates a Notion page with Description, Timeline, and Resolution sections.

See [incident-workflow.md](references/incident-workflow.md) for the complete workflow YAML and database schema.

Quick trigger:

```bash
gh workflow run notion-incident.yml \
  -f severity=P1 \
  -f title="Database connection pool exhausted" \
  -f description="Production DB hit max connections at 14:32 UTC"
```

### Changelog Page Updater

Parse `CHANGELOG.md` and replace a Notion page's content with structured blocks (headings, bullet lists, paragraphs). Clears existing content first, then appends in 100-block chunks with rate-limit delays.

See [changelog-sync.md](references/changelog-sync.md) for the complete Node.js script and GitHub Actions step.

## Resources

- [Notion API Reference](https://developers.notion.com/reference/intro)
- [@notionhq/client on npm](https://www.npmjs.com/package/@notionhq/client)
- [notion-client on PyPI](https://pypi.org/project/notion-client/)
- [GitHub Actions Encrypted Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Notion Request Limits (3 req/sec)](https://developers.notion.com/reference/request-limits)
- [GitHub Actions Workflow Syntax](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)

## Next Steps

For deployment patterns and environment-specific Notion sync, see `notion-deploy-integration`. For rate limit handling strategies at scale, see `notion-rate-limits`.
