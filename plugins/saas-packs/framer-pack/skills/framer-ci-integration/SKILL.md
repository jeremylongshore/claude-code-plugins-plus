---
name: framer-ci-integration
description: |
  Configure Framer CI/CD integration with GitHub Actions and testing.
  Use when setting up automated testing, configuring CI pipelines,
  or integrating Framer tests into your build process.
  Trigger with phrases like "framer CI", "framer GitHub Actions",
  "framer automated tests", "CI framer".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, framer]
compatible-with: claude-code
---

# Framer CI Integration

## Overview

Set up CI/CD for Framer plugins and Server API integrations. Plugin builds are tested with Vite + vitest. Server API CMS sync can be triggered from CI for automated content publishing.

## Instructions

### Step 1: GitHub Actions for Plugin Build

```yaml
name: Framer Plugin CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20', cache: 'npm' }
      - run: npm ci
      - run: npm run build
      - run: npm test

  cms-sync:
    if: github.ref == 'refs/heads/main'
    needs: build
    runs-on: ubuntu-latest
    env:
      FRAMER_API_KEY: ${{ secrets.FRAMER_API_KEY }}
      FRAMER_SITE_ID: ${{ secrets.FRAMER_SITE_ID }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20', cache: 'npm' }
      - run: npm ci
      - name: Sync CMS and publish
        run: node scripts/sync-and-publish.js
```

### Step 2: CMS Sync Script for CI

```typescript
// scripts/sync-and-publish.ts
import { framer } from 'framer-api';

async function main() {
  const client = await framer.connect({
    apiKey: process.env.FRAMER_API_KEY!,
    siteId: process.env.FRAMER_SITE_ID!,
  });

  // Fetch content from your CMS/API
  const posts = await fetch('https://your-api.com/posts').then(r => r.json());

  // Sync to Framer CMS
  const collections = await client.getCollections();
  const blogCollection = collections.find(c => c.name === 'Blog Posts');
  if (blogCollection) {
    await blogCollection.setItems(posts.map(p => ({ fieldData: { title: p.title, body: p.content, slug: p.slug } })));
    console.log(`Synced ${posts.length} posts`);
  }

  // Publish site
  await client.publish();
  console.log('Site published');
}

main().catch(e => { console.error(e); process.exit(1); });
```

### Step 3: Configure Secrets

```bash
gh secret set FRAMER_API_KEY --body "framer_sk_..."
gh secret set FRAMER_SITE_ID --body "abc123"
```

## Output

- Plugin builds verified on every PR
- Automated CMS sync and publish on main push
- Secrets configured in GitHub

## Resources

- [GitHub Actions](https://docs.github.com/en/actions)
- [Framer Server API](https://www.framer.com/developers/server-api-introduction)

## Next Steps

For deployment, see `framer-deploy-integration`.
