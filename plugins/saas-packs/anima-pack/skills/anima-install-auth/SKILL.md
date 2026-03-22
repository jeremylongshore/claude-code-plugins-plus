---
name: anima-install-auth
description: |
  Install the Anima SDK and configure authentication for Figma-to-code generation.
  Use when setting up design-to-code automation, configuring Figma token access,
  or initializing the @animaapp/anima-sdk for server-side code generation.
  Trigger: "install anima", "setup anima", "anima auth", "anima figma token".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, figma, anima, code-generation]
compatible-with: claude-code
---

# Anima Install & Auth

## Overview

Install `@animaapp/anima-sdk` and configure authentication tokens. Anima converts Figma designs into production-ready React, Vue, or HTML code with Tailwind, MUI, AntD, or shadcn styling. The SDK runs server-side only.

## Prerequisites

- Node.js 18+ (SDK is server-side only)
- Figma account with API access
- Anima API token (request at [animaapp.com](https://www.animaapp.com))
- Figma Personal Access Token

## Instructions

### Step 1: Install the Anima SDK

```bash
npm install @animaapp/anima-sdk
```

### Step 2: Get Your Tokens

```bash
# 1. Figma Personal Access Token:
#    Figma > Settings > Account > Personal Access Tokens > Generate

# 2. Anima API Token:
#    Request from Anima team (currently limited partner access)
#    https://docs.animaapp.com/docs/anima-api

# Store securely
cat > .env << 'EOF'
ANIMA_TOKEN=your-anima-api-token
FIGMA_TOKEN=your-figma-personal-access-token
EOF

echo ".env" >> .gitignore
chmod 600 .env
```

### Step 3: Initialize and Verify

```typescript
// src/anima-client.ts
import { Anima } from '@animaapp/anima-sdk';

const anima = new Anima({
  auth: {
    token: process.env.ANIMA_TOKEN!,
  },
});

// Verify connection by generating code from a known Figma file
async function verifySetup() {
  try {
    const { files } = await anima.generateCode({
      fileKey: 'your-figma-file-key',     // From Figma URL: figma.com/file/{fileKey}/...
      figmaToken: process.env.FIGMA_TOKEN!,
      nodesId: ['1:2'],                    // Specific node to convert
      settings: {
        language: 'typescript',
        framework: 'react',
        styling: 'tailwind',
      },
    });

    console.log(`Generated ${files.length} files`);
    for (const file of files) {
      console.log(`  ${file.fileName} (${file.content.length} chars)`);
    }
    return true;
  } catch (error) {
    console.error('Setup verification failed:', error);
    return false;
  }
}

verifySetup();
```

### Step 4: Get Your Figma File Key

```
Figma URL format:
https://www.figma.com/file/ABC123xyz/My-Design?node-id=1:2

File Key: ABC123xyz
Node ID: 1:2 (from the URL query parameter)
```

## Output

- `@animaapp/anima-sdk` installed
- Anima token and Figma token configured in `.env`
- Verified code generation from a Figma design
- Understanding of file key and node ID extraction

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Invalid Anima token` | Token not provisioned | Request token from Anima team |
| `Invalid Figma token` | PAT expired or wrong | Generate new PAT in Figma Settings |
| `File not found` | Wrong file key | Extract key from Figma URL correctly |
| `Node not found` | Invalid node ID | Use Figma Dev Mode to get node IDs |
| `SDK not for browser` | Used in client-side code | SDK is server-side only |

## Resources

- [Anima API Docs](https://docs.animaapp.com/docs/anima-api)
- [Anima SDK GitHub](https://github.com/AnimaApp/anima-sdk)
- [Figma API Auth](https://www.figma.com/developers/api#access-tokens)
- [Anima npm](https://www.npmjs.com/package/@animaapp/anima-sdk)

## Next Steps

Proceed to `anima-hello-world` for your first design-to-code conversion.
