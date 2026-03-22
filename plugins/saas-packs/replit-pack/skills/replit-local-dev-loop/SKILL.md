---
name: replit-local-dev-loop
description: |
  Configure Replit development workflow with hot reload, Webview, and Replit Agent.
  Use when setting up dev server, configuring run commands, debugging in Workspace,
  or using Replit Agent for AI-assisted development.
  Trigger with phrases like "replit dev server", "replit hot reload",
  "replit local development", "replit agent", "replit workflow".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, replit, development, workflow, agent]

---
# Replit Local Dev Loop

## Overview
Configure the Replit Workspace development cycle: run commands, hot reloading, port configuration, Webview preview, dev/production database separation, and Replit Agent for AI-assisted building.

## Prerequisites
- Replit App with `.replit` configured
- Node.js or Python project initialized
- Familiarity with Replit Workspace UI

## Instructions

### Step 1: Configure Run Commands
```toml
# .replit — run determines what happens when you click "Run"

# Simple string command
run = "npm run dev"

# Array form (recommended for deployment)
# run = ["sh", "-c", "npm run dev"]

# Multiple services simultaneously
# run = "npm run api & npm run frontend & wait"

entrypoint = "index.ts"
```

**Compiled languages** need a compile step:
```toml
# TypeScript
compile = "npx tsc -b"
run = "node dist/index.js"

# Go
compile = "go build -o main ."
run = "./main"
```

### Step 2: Hot Reload Setup

**Node.js with tsx watch:**
```toml
# .replit
run = "npx tsx watch src/index.ts"
```

```json
{
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "test": "vitest",
    "test:watch": "vitest --watch"
  }
}
```

**Python with Flask auto-reload:**
```toml
run = "python main.py"

[env]
FLASK_DEBUG = "1"
```

```python
# main.py — Flask auto-reloads in debug mode
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
```

**Vite/Next.js dev server:**
```toml
run = "npm run dev"

[env]
PORT = "3000"
```

### Step 3: Port Configuration
Replit routes external traffic to your app's port. Your app must listen on `0.0.0.0`:

```typescript
// Correct — Replit can reach this
app.listen(3000, '0.0.0.0', () => console.log('Ready'));

// Wrong — unreachable from Webview
// app.listen(3000, '127.0.0.1', () => ...);
```

```toml
[deployment]
run = ["sh", "-c", "npm start"]
deploymentTarget = "autoscale"
# Ignore ports used by dev tools only
ignorePorts = [3001, 5555]
```

Use the Networking tool in the sidebar to view active port mappings.

### Step 4: Dev vs Production Database
Replit provides separate development and production databases:

```typescript
// Databases auto-switch based on context:
// - Workspace "Run" button -> development database
// - Deployed app -> production database
// Both use the same DATABASE_URL env var — no code changes needed

import { Pool } from 'pg';
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false },
});
```

View database settings in the PostgreSQL pane:
- **Development tab**: data for workspace testing
- **Production tab**: live customer data (only after deployment)

### Step 5: Using Replit Agent
Replit Agent (v4) builds apps from natural language prompts. It creates files, installs packages, runs tests, and can work up to 200 minutes autonomously.

```markdown
Effective Agent prompts:
- "Build a todo app with user auth, PostgreSQL, and a React frontend"
- "Add a /api/search endpoint with full-text search"
- "Fix the login flow - users lose auth after redirect"

Agent 4 features:
- Parallel task forks (splits work, combines results)
- Self-testing and error correction
- Full .replit and replit.nix configuration
- Works with any framework
```

### Step 6: Testing in Workspace
```toml
# .replit
[unitTest]
language = "nodejs"
```

```typescript
// __tests__/api.test.ts
import { describe, it, expect } from 'vitest';

describe('Health Check', () => {
  it('returns ok', async () => {
    const res = await fetch('http://localhost:3000/health');
    expect(res.ok).toBe(true);
  });
});
```

### Development Workflow Summary
```
1. Edit code in Workspace editor
2. Click "Run" -> dev server starts with hot reload
3. Webview tab shows live preview
4. Console tab shows server logs
5. Shell tab for CLI commands
6. Secrets tab (lock icon) for env vars
7. Database pane for PostgreSQL / KV data
8. Deploy when ready -> production database activates
```

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Webview blank | App not on 0.0.0.0 | Bind to `0.0.0.0`, not `localhost` |
| Port already in use | Previous run active | Click "Stop" then "Run" |
| Module not found | Package missing | Use Packages tool or `npm install` |
| Hot reload broken | Wrong run command | Use `tsx watch` or `nodemon` |
| Agent stalls | Complex prompt | Break into smaller requests |

## Resources
- [Configuring Your Repl](https://docs.replit.com/replit-workspace/configuring-repl)
- [Replit Agent](https://docs.replit.com/replitai/agent)
- [Database FAQ](https://docs.replit.com/hosting/database-faq)

## Next Steps
See `replit-sdk-patterns` for production code patterns or `replit-deploy-integration` to deploy.
