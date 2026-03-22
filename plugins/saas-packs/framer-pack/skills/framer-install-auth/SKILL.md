---
name: framer-install-auth
description: |
  Install and configure Framer SDK/CLI authentication.
  Use when setting up a new Framer integration, configuring API keys,
  or initializing Framer in your project.
  Trigger with phrases like "install framer", "setup framer",
  "framer auth", "configure framer API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, framer]
compatible-with: claude-code
---

# Framer Install & Auth

## Overview

Set up the Framer Plugin SDK for building editor plugins, or the `framer-api` package for Server API access. Framer has two developer surfaces: **Plugins** (run inside the Framer editor UI) and **Server API** (run from any Node.js server via WebSocket).

## Prerequisites

- Node.js 18+
- Framer account (free or paid)
- For Server API: API key from site settings

## Instructions

### Step 1: Choose Your Integration Type

| Type | Package | Use Case |
|------|---------|----------|
| Plugin | `framer-plugin` | UI that runs inside Framer editor |
| Server API | `framer-api` | Headless CMS sync, CI/CD publishing |
| Code Components | React in Framer | Custom components on the canvas |
| Code Overrides | React in Framer | Modify existing component behavior |

### Step 2: Set Up a Framer Plugin

```bash
# Scaffold a new plugin project
npx create-framer-plugin@latest my-plugin
cd my-plugin
npm install
npm run dev
```

This creates a Vite + React project with the `framer-plugin` package pre-configured. The plugin runs inside Framer's editor iframe.

### Step 3: Set Up the Server API (Headless Access)

```bash
npm install framer-api
```

```typescript
// server.ts — Server API connection
import { framer } from 'framer-api';

const client = await framer.connect({
  apiKey: process.env.FRAMER_API_KEY!, // From site settings
  siteId: process.env.FRAMER_SITE_ID!,
});

// List all CMS collections
const collections = await client.getCollections();
console.log('Collections:', collections.map(c => c.name));
```

### Step 4: Configure Environment Variables

```bash
# .env (NEVER commit)
FRAMER_API_KEY=framer_sk_abc123...
FRAMER_SITE_ID=abc123def456

# .gitignore
.env
.env.local
```

### Step 5: Verify Plugin Connection

Open Framer, go to your project, click Plugins > Development > select your local plugin. The dev server hot-reloads into the editor.

```typescript
// Plugin verification — runs inside Framer editor
import { framer } from 'framer-plugin';

export function App() {
  const handleTest = async () => {
    const selection = await framer.getSelection();
    console.log('Selected layers:', selection.length);
    framer.notify(`Found ${selection.length} selected layers`);
  };

  return <button onClick={handleTest}>Test Connection</button>;
}
```

## Output

- Plugin project scaffolded with Vite + React
- Server API client connected via WebSocket
- Environment variables configured
- Verified connection to Framer editor or API

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Plugin not showing` | Dev server not running | Run `npm run dev` and reload Framer |
| `Invalid API key` | Wrong key or site ID | Generate new key in site settings |
| `WebSocket connection failed` | Network/firewall | Allow outbound WSS connections |
| `framer-plugin not found` | Missing dependency | Run `npm install framer-plugin` |

## Resources

- [Framer Plugin Introduction](https://www.framer.com/developers/plugins-introduction)
- [Server API Quick Start](https://www.framer.com/developers/server-api-quick-start)
- [Framer API Reference](https://www.framer.com/developers/reference)

## Next Steps

After setup, proceed to `framer-hello-world` for your first plugin or component.
