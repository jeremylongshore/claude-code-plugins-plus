# Incident Report Creator — GitHub Actions Workflow

Complete `workflow_dispatch` workflow that creates structured incident pages in a Notion database from CI. Dispatched manually with severity, title, and description inputs.

## Workflow File

```yaml
# .github/workflows/notion-incident.yml
name: Create Incident Report

on:
  workflow_dispatch:
    inputs:
      severity:
        description: 'Incident severity'
        required: true
        type: choice
        options: [P1, P2, P3]
      title:
        description: 'Incident title'
        required: true
      description:
        description: 'What happened'
        required: true

jobs:
  create-incident:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci

      - name: Create incident page in Notion
        run: |
          node -e "
          const { Client } = require('@notionhq/client');
          const notion = new Client({ auth: process.env.NOTION_TOKEN });

          (async () => {
            const page = await notion.pages.create({
              parent: { database_id: process.env.NOTION_INCIDENTS_DB },
              properties: {
                Name: { title: [{ text: { content: process.env.TITLE } }] },
                Severity: { select: { name: process.env.SEVERITY } },
                Status: { select: { name: 'Investigating' } },
                'Reported At': { date: { start: new Date().toISOString() } },
                Reporter: { rich_text: [{ text: { content: process.env.GITHUB_ACTOR } }] },
                'Run URL': { url: process.env.RUN_URL },
              },
            });

            await notion.blocks.children.append({
              block_id: page.id,
              children: [
                { heading_2: { rich_text: [{ text: { content: 'Description' } }] } },
                { paragraph: { rich_text: [{ text: { content: process.env.DESCRIPTION } }] } },
                { heading_2: { rich_text: [{ text: { content: 'Timeline' } }] } },
                { paragraph: { rich_text: [{ text: { content: new Date().toISOString() + ' — Incident created from CI' } }] } },
                { heading_2: { rich_text: [{ text: { content: 'Resolution' } }] } },
                { paragraph: { rich_text: [{ text: { content: 'Pending investigation...' } }] } },
              ],
            });

            console.log('Incident page created: ' + page.url);
          })();
          "
        env:
          NOTION_TOKEN: ${{ secrets.NOTION_TOKEN }}
          NOTION_INCIDENTS_DB: ${{ secrets.NOTION_INCIDENTS_DB }}
          TITLE: ${{ inputs.title }}
          SEVERITY: ${{ inputs.severity }}
          DESCRIPTION: ${{ inputs.description }}
          RUN_URL: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}
```

## Required Notion Database Schema

| Property | Type | Values |
|----------|------|--------|
| Name | Title | Free text |
| Severity | Select | P1, P2, P3 |
| Status | Select | Investigating, Mitigated, Resolved |
| Reported At | Date | ISO timestamp |
| Reporter | Rich Text | GitHub username |
| Run URL | URL | Actions run link |

## Usage

Trigger from the GitHub Actions UI or via CLI:

```bash
gh workflow run notion-incident.yml \
  -f severity=P1 \
  -f title="Database connection pool exhausted" \
  -f description="Production DB hit max connections at 14:32 UTC"
```
