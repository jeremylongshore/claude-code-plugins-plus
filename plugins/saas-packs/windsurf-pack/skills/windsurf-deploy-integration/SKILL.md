---
name: windsurf-deploy-integration
description: |
  Deploy Windsurf integrations to Vercel, Fly.io, and Cloud Run platforms.
  Use when deploying Windsurf-powered applications to production,
  configuring platform-specific secrets, or setting up deployment pipelines.
  Trigger with phrases like "deploy windsurf", "windsurf Vercel",
  "windsurf production deploy", "windsurf Cloud Run", "windsurf Fly.io".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Windsurf Deploy Integration

## Overview
Deploy Windsurf extensions and configurations to teams. Windsurf, as a VS Code-based IDE, uses the standard extension deployment model. Covers packaging extensions with `vsce`, publishing to marketplaces, and distributing team-wide Windsurf configurations via shared settings and extension packs.

## Prerequisites
- Node.js and npm installed
- `vsce` CLI for extension packaging (`npm install -g @vscode/vsce`)
- Windsurf extension project with `package.json`
- Marketplace publisher account (for public distribution)

## Instructions

### Step 1: Package Extension
```bash
# Install vsce
npm install -g @vscode/vsce

# Package extension as .vsix
cd my-windsurf-extension
vsce package

# Output: my-extension-1.0.0.vsix
```

### Step 2: Extension package.json
```json
{
  "name": "my-windsurf-extension",
  "displayName": "My Windsurf Extension",
  "version": "1.0.0",
  "engines": {
    "vscode": "^1.85.0"
  },
  "activationEvents": ["onStartupFinished"],
  "main": "./dist/extension.js",
  "contributes": {
    "commands": [{
      "command": "myext.activate",
      "title": "Activate My Extension"
    }],
    "configuration": {
      "title": "My Extension",
      "properties": {
        "myext.apiKey": {
          "type": "string",
          "description": "API key for backend service"
        }
      }
    }
  },
  "scripts": {
    "build": "tsc -p ./",
    "package": "vsce package",
    "publish": "vsce publish"
  }
}
```

### Step 3: Distribute to Team
```bash
# Install .vsix manually in Windsurf
# Extensions sidebar > "..." menu > "Install from VSIX..."

# Or via command line
code --install-extension my-extension-1.0.0.vsix
```

### Step 4: Shared Team Settings
```json
// .vscode/settings.json (commit to repo)
{
  "myext.apiKey": "",
  "editor.formatOnSave": true,
  "windsurf.cascade.enabled": true
}
```

```json
// .vscode/extensions.json (recommended extensions)
{
  "recommendations": [
    "publisher.my-windsurf-extension",
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode"
  ]
}
```

### Step 5: CI/CD for Extension
```yaml
# .github/workflows/publish.yml
name: Publish Extension
on:
  push:
    tags: ["v*"]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: npm ci && npm run build
      - run: npx vsce package
      - run: npx vsce publish
        env:
          VSCE_PAT: ${{ secrets.VSCE_PAT }}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Package fails | Missing files | Check `files` field in package.json |
| Extension not loading | Wrong engine version | Match `engines.vscode` to Windsurf version |
| Settings not applied | Wrong scope | Use workspace vs user settings appropriately |
| Publish rejected | Invalid publisher | Create publisher at marketplace.visualstudio.com |

## Examples

### Quick Package and Install
```bash
npm run build && vsce package && code --install-extension *.vsix
```

## Resources
- [VS Code Extension Publishing](https://code.visualstudio.com/api/working-with-extensions/publishing-extension)
- [Windsurf Documentation](https://docs.windsurf.ai)

## Next Steps
For multi-environment setup, see `windsurf-multi-env-setup`.
