# GitHub Actions Workflow for Documentation Sync

Push changelogs and release notes to Notion automatically on release. This workflow
runs three jobs: create a release-notes page on `release: published`, sync the
`CHANGELOG.md` page on push to `main`, and update the deploy tracker after the
release-notes job succeeds.

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
