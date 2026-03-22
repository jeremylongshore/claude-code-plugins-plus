---
name: anima-ci-integration
description: |
  Configure CI/CD pipeline for automated Figma-to-code generation with Anima.
  Use when automating design-to-code in GitHub Actions, setting up PR-based
  component generation, or integrating Anima into design handoff workflows.
  Trigger: "anima CI", "anima GitHub Actions", "anima automated generation".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, figma, anima, ci-cd]
compatible-with: claude-code
---

# Anima CI Integration

## Instructions

### Step 1: GitHub Actions Workflow

```yaml
# .github/workflows/design-sync.yml
name: Design-to-Code Sync

on:
  schedule:
    - cron: '0 9 * * 1-5'  # Weekdays at 9am
  workflow_dispatch:         # Manual trigger

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: npm ci
      - name: Generate components from Figma
        env:
          ANIMA_TOKEN: ${{ secrets.ANIMA_TOKEN }}
          FIGMA_TOKEN: ${{ secrets.FIGMA_TOKEN }}
          FIGMA_FILE_KEY: ${{ secrets.FIGMA_FILE_KEY }}
        run: npx tsx scripts/generate-components.ts
      - name: Lint generated code
        run: npx eslint src/components/generated/ --fix
      - name: Check for changes
        id: changes
        run: |
          if git diff --quiet src/components/generated/; then
            echo "changed=false" >> $GITHUB_OUTPUT
          else
            echo "changed=true" >> $GITHUB_OUTPUT
          fi
      - name: Create PR with generated components
        if: steps.changes.outputs.changed == 'true'
        run: |
          git checkout -b design-sync/$(date +%Y%m%d)
          git add src/components/generated/
          git commit -m "chore: sync generated components from Figma"
          git push -u origin HEAD
          gh pr create --title "Design sync: updated generated components" \
            --body "Auto-generated from Figma via Anima SDK"
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### Step 2: Generation Script for CI

```typescript
// scripts/generate-components.ts
import { Anima } from '@animaapp/anima-sdk';
import fs from 'fs';

const anima = new Anima({ auth: { token: process.env.ANIMA_TOKEN! } });

const COMPONENTS = [
  { nodeId: '1:2', name: 'Hero' },
  { nodeId: '3:4', name: 'Card' },
  { nodeId: '5:6', name: 'Navigation' },
];

async function main() {
  const outputDir = 'src/components/generated';
  fs.mkdirSync(outputDir, { recursive: true });

  for (const comp of COMPONENTS) {
    const { files } = await anima.generateCode({
      fileKey: process.env.FIGMA_FILE_KEY!,
      figmaToken: process.env.FIGMA_TOKEN!,
      nodesId: [comp.nodeId],
      settings: { language: 'typescript', framework: 'react', styling: 'tailwind', uiLibrary: 'shadcn' },
    });

    for (const file of files) {
      fs.writeFileSync(`${outputDir}/${file.fileName}`, file.content);
    }
    console.log(`Generated: ${comp.name}`);
    await new Promise(r => setTimeout(r, 6000)); // Rate limit
  }
}

main().catch(err => { console.error(err); process.exit(1); });
```

## Output

- Scheduled GitHub Actions workflow for design-to-code sync
- Auto-PR creation when generated code changes
- ESLint auto-fix on generated output
- Rate-limited generation script for CI

## Resources

- [Anima API](https://docs.animaapp.com/docs/anima-api)
- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)

## Next Steps

For deployment, see `anima-deploy-integration`.
