# CI Scripts for Notion Operations

Three drop-in scripts the workflow calls: a release-notes sync and a deploy-status
update in Node.js, plus a Python batch updater for bulk status changes. All handle
the Notion 3-requests/second limit with sequential calls and delays.

## Release Notes Sync (Node.js)

Creates a page in the releases database and appends the release body as paragraph
blocks, batching in chunks of 100 (the Notion per-request block limit) with a 350ms
delay between batches.

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

## Deploy Status Update (Node.js)

Upserts a deploy entry: query the deploys database by version, then update the
existing page or create a new one with status, environment, timestamp, and the
short commit SHA.

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

## Python Batch Update Script for CI

Bulk-updates every entry matching a filter — for example flipping all "In Progress"
rows to "Deployed" after a release. Ships a `--dry-run` mode and honors the
`retry-after` header on 429s.

```python
#!/usr/bin/env python3
# scripts/notion_batch_update.py
"""Batch update Notion database entries from CI.

Usage:
  python3 scripts/notion_batch_update.py --database-id DBID \
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
