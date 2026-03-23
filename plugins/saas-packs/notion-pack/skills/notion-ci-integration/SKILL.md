---
name: notion-ci-integration
description: |
  Integrate the Notion API into CI/CD pipelines for automated documentation sync,
  deploy tracking, and configuration reads. Use when setting up GitHub Actions
  workflows that push release notes to Notion, update database entries on deploy,
  create incident pages from CI, or read feature flags from Notion databases.
  Trigger with phrases like "notion CI", "notion GitHub Actions", "notion deploy sync",
  "notion release notes automation", "notion CI pipeline".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(npm:*), Bash(npx:*), Bash(python3:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, notion, ci-cd, devops]
compatible-with: claude-code
---

# Notion CI Integration

## Overview

Automate documentation sync, deploy tracking, and configuration management by integrating the Notion API into CI/CD pipelines. This skill covers GitHub Actions workflows that push changelogs and release notes to Notion pages, update database entries on successful deploys, create pages for incident reports, and read feature flags or configuration from Notion databases — all with proper rate limit handling for CI environments.

## Prerequisites

- GitHub repository with Actions enabled
- Notion internal integration token (create at `https://www.notion.so/my-integrations`)
- Target Notion pages/databases shared with the integration (click "..." > "Connections" > add your integration)
- `NOTION_TOKEN` stored as a GitHub Actions secret
- Node.js 18+ or Python 3.9+ in CI environment

## Instructions

### Step 1: GitHub Actions Workflow for Documentation Sync

Push changelogs and release notes to Notion automatically on release.

```yaml
# .github/workflows/notion-docs-sync.yml
name: Sync Docs to Notion

on:
  release:
    types: [published]
  push:
    branches: [main]
    paths: ['CHANGELOG.md', 'docs/**']

env:
  NOTION_TOKEN: ${{ secrets.NOTION_TOKEN }}

jobs:
  sync-release-notes:
    runs-on: ubuntu-latest
    if: github.event_name == 'release'
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci

      - name: Push release notes to Notion
        run: node scripts/notion-release-sync.js
        env:
          NOTION_RELEASES_DB: ${{ secrets.NOTION_RELEASES_DB }}
          RELEASE_TAG: ${{ github.event.release.tag_name }}
          RELEASE_BODY: ${{ github.event.release.body }}
          RELEASE_URL: ${{ github.event.release.html_url }}

  sync-changelog:
    runs-on: ubuntu-latest
    if: github.event_name == 'push'
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci

      - name: Sync CHANGELOG to Notion page
        run: node scripts/notion-changelog-sync.js
        env:
          NOTION_CHANGELOG_PAGE: ${{ secrets.NOTION_CHANGELOG_PAGE }}

  update-deploy-status:
    runs-on: ubuntu-latest
    needs: sync-release-notes
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci

      - name: Update deploy tracker in Notion
        run: node scripts/notion-deploy-update.js
        env:
          NOTION_DEPLOYS_DB: ${{ secrets.NOTION_DEPLOYS_DB }}
          DEPLOY_VERSION: ${{ github.event.release.tag_name }}
          DEPLOY_ENV: production
          DEPLOY_SHA: ${{ github.sha }}
```

### Step 2: CI Scripts for Notion Operations

#### Release Notes Sync (Node.js)

```typescript
// scripts/notion-release-sync.js
import { Client } from '@notionhq/client';

const notion = new Client({ auth: process.env.NOTION_TOKEN });
const databaseId = process.env.NOTION_RELEASES_DB;

async function syncReleaseNotes() {
  const tag = process.env.RELEASE_TAG;
  const body = process.env.RELEASE_BODY || 'No release notes provided.';
  const url = process.env.RELEASE_URL;

  // Create a new page in the releases database
  const page = await notion.pages.create({
    parent: { database_id: databaseId },
    properties: {
      Name: {
        title: [{ text: { content: `Release ${tag}` } }],
      },
      Version: {
        rich_text: [{ text: { content: tag } }],
      },
      Status: {
        select: { name: 'Released' },
      },
      'Release Date': {
        date: { start: new Date().toISOString().split('T')[0] },
      },
      'GitHub URL': {
        url: url,
      },
    },
  });

  // Append the release body as page content
  const blocks = body.split('\n').filter(Boolean).map((line) => ({
    paragraph: {
      rich_text: [{ text: { content: line } }],
    },
  }));

  // Notion API limits to 100 blocks per request
  for (let i = 0; i < blocks.length; i += 100) {
    await notion.blocks.children.append({
      block_id: page.id,
      children: blocks.slice(i, i + 100),
    });
    // Rate limit: wait between batch appends
    if (i + 100 < blocks.length) await sleep(350);
  }

  console.log(`Created release page: ${page.id}`);
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

syncReleaseNotes().catch((err) => {
  console.error('Failed to sync release notes:', err.message);
  process.exit(1);
});
```

#### Deploy Status Update (Node.js)

```typescript
// scripts/notion-deploy-update.js
import { Client } from '@notionhq/client';

const notion = new Client({ auth: process.env.NOTION_TOKEN });
const databaseId = process.env.NOTION_DEPLOYS_DB;

async function updateDeployStatus() {
  const version = process.env.DEPLOY_VERSION;
  const environment = process.env.DEPLOY_ENV || 'staging';
  const sha = process.env.DEPLOY_SHA;

  // Search for existing entry by version
  const existing = await notion.databases.query({
    database_id: databaseId,
    filter: {
      property: 'Version',
      rich_text: { equals: version },
    },
  });

  if (existing.results.length > 0) {
    // Update existing entry
    await notion.pages.update({
      page_id: existing.results[0].id,
      properties: {
        Status: { select: { name: 'Deployed' } },
        Environment: { select: { name: environment } },
        'Deploy Time': {
          date: { start: new Date().toISOString() },
        },
        'Commit SHA': {
          rich_text: [{ text: { content: sha.substring(0, 7) } }],
        },
      },
    });
    console.log(`Updated deploy entry for ${version}`);
  } else {
    // Create new deploy entry
    await notion.pages.create({
      parent: { database_id: databaseId },
      properties: {
        Name: {
          title: [{ text: { content: `Deploy ${version}` } }],
        },
        Version: {
          rich_text: [{ text: { content: version } }],
        },
        Status: { select: { name: 'Deployed' } },
        Environment: { select: { name: environment } },
        'Deploy Time': {
          date: { start: new Date().toISOString() },
        },
        'Commit SHA': {
          rich_text: [{ text: { content: sha.substring(0, 7) } }],
        },
      },
    });
    console.log(`Created deploy entry for ${version}`);
  }
}

updateDeployStatus().catch((err) => {
  console.error('Failed to update deploy status:', err.message);
  process.exit(1);
});
```

#### Python Batch Update Script for CI

```python
#!/usr/bin/env python3
# scripts/notion_batch_update.py
"""Batch update Notion database entries from CI.

Usage:
  python3 scripts/notion_batch_update.py --database-id <id> \
    --filter-property Status --filter-value "In Progress" \
    --set-property Status --set-value "Deployed" \
    --set-property Version --set-value "$TAG"
"""
import os
import sys
import time
import argparse
from notion_client import Client, APIResponseError

RATE_LIMIT_DELAY = 0.34  # 3 requests/sec max

def main():
    parser = argparse.ArgumentParser(description='Batch update Notion DB entries')
    parser.add_argument('--database-id', required=True)
    parser.add_argument('--filter-property', required=True)
    parser.add_argument('--filter-value', required=True)
    parser.add_argument('--set-property', action='append', required=True)
    parser.add_argument('--set-value', action='append', required=True)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    token = os.environ.get('NOTION_TOKEN')
    if not token:
        print('ERROR: NOTION_TOKEN not set', file=sys.stderr)
        sys.exit(1)

    notion = Client(auth=token)

    # Query with filter
    results = []
    cursor = None
    while True:
        response = notion.databases.query(
            database_id=args.database_id,
            filter={
                'property': args.filter_property,
                'select': {'equals': args.filter_value},
            },
            start_cursor=cursor,
        )
        results.extend(response['results'])
        if not response['has_more']:
            break
        cursor = response['next_cursor']
        time.sleep(RATE_LIMIT_DELAY)

    print(f'Found {len(results)} entries matching {args.filter_property}={args.filter_value}')

    if args.dry_run:
        for page in results:
            title = page['properties'].get('Name', {}).get('title', [{}])
            name = title[0].get('plain_text', 'Untitled') if title else 'Untitled'
            print(f'  Would update: {name} ({page["id"]})')
        return

    # Build update properties
    updates = {}
    for prop, val in zip(args.set_property, args.set_value):
        updates[prop] = {'select': {'name': val}}

    # Apply updates sequentially (rate limit safe)
    success = 0
    for page in results:
        try:
            notion.pages.update(page_id=page['id'], properties=updates)
            success += 1
            time.sleep(RATE_LIMIT_DELAY)
        except APIResponseError as e:
            if e.code == 'rate_limited':
                retry_after = float(e.headers.get('retry-after', 1))
                print(f'Rate limited. Waiting {retry_after}s...')
                time.sleep(retry_after)
                notion.pages.update(page_id=page['id'], properties=updates)
                success += 1
            else:
                print(f'Failed to update {page["id"]}: {e.message}', file=sys.stderr)

    print(f'Updated {success}/{len(results)} entries')

if __name__ == '__main__':
    main()
```

### Step 3: Reading Configuration from Notion in CI

Use Notion databases as a lightweight feature-flag or config store that non-engineers can edit.

```typescript
// scripts/notion-read-config.js
import { Client } from '@notionhq/client';
import { writeFileSync } from 'fs';

const notion = new Client({ auth: process.env.NOTION_TOKEN });
const configDbId = process.env.NOTION_CONFIG_DB;

async function readConfig() {
  const response = await notion.databases.query({
    database_id: configDbId,
    filter: {
      property: 'Environment',
      select: { equals: process.env.DEPLOY_ENV || 'production' },
    },
  });

  const config = {};
  for (const page of response.results) {
    if (page.object !== 'page' || !('properties' in page)) continue;
    const props = page.properties;

    const keyProp = props['Key'];
    const valueProp = props['Value'];
    if (keyProp?.type !== 'title' || valueProp?.type !== 'rich_text') continue;

    const key = keyProp.title.map((t) => t.plain_text).join('');
    const value = valueProp.rich_text.map((t) => t.plain_text).join('');

    if (key) config[key] = value;
  }

  // Write config to file for downstream CI steps
  writeFileSync('notion-config.json', JSON.stringify(config, null, 2));
  console.log(`Loaded ${Object.keys(config).length} config entries from Notion`);
}

readConfig().catch((err) => {
  console.error('Failed to read config:', err.message);
  process.exit(1);
});
```

GitHub Actions step to consume:

```yaml
- name: Load feature flags from Notion
  run: node scripts/notion-read-config.js
  env:
    NOTION_TOKEN: ${{ secrets.NOTION_TOKEN }}
    NOTION_CONFIG_DB: ${{ secrets.NOTION_CONFIG_DB }}
    DEPLOY_ENV: production

- name: Use config in build
  run: |
    CONFIG=$(cat notion-config.json)
    echo "Feature flags loaded: $(echo $CONFIG | jq 'keys | length') entries"
```

## Output

- GitHub Actions workflow that syncs release notes to a Notion database on every release
- Deploy tracker that updates database entries with status "Deployed", version tag, commit SHA, and timestamp
- Python batch update script for bulk status changes in CI (with `--dry-run` safety)
- Config reader that pulls feature flags from Notion databases into CI environment
- All scripts handle rate limits (sequential operations, 350ms delays between requests)

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
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
