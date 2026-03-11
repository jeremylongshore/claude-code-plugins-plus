---
name: langfuse-install-auth
description: |
  Install and configure Langfuse SDK authentication for LLM observability.
  Use when setting up a new Langfuse integration, configuring API keys,
  or initializing Langfuse tracing in your project.
  Trigger with phrases like "install langfuse", "setup langfuse",
  "langfuse auth", "configure langfuse API key", "langfuse tracing setup".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Bash(pnpm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Langfuse Install & Auth

## Overview
Set up Langfuse SDK and configure authentication for LLM observability and tracing.

## Prerequisites
- Node.js 18+ or Python 3.9+
- Package manager (npm, pnpm, or pip)
- Langfuse account (cloud or self-hosted)
- Public and Secret keys from Langfuse dashboard

## Instructions

### Step 1: Install SDK

```bash
set -euo pipefail
# Node.js / TypeScript
npm install langfuse
# or
pnpm add langfuse

# Python
pip install langfuse
```

### Step 2: Get API Keys

1. Go to Langfuse dashboard (https://cloud.langfuse.com or your self-hosted instance)
2. Navigate to Settings -> API Keys
3. Create new API key pair (Public Key + Secret Key)
4. Note your host URL (cloud: `https://cloud.langfuse.com`)

### Step 3: Configure Authentication

```bash
# Set environment variables
export LANGFUSE_PUBLIC_KEY="pk-lf-..."
export LANGFUSE_SECRET_KEY="sk-lf-..."
export LANGFUSE_HOST="https://cloud.langfuse.com"  # or self-hosted URL

# Or create .env file
cat >> .env << 'EOF'
LANGFUSE_PUBLIC_KEY=pk-lf-your-public-key
LANGFUSE_SECRET_KEY=sk-lf-your-secret-key
LANGFUSE_HOST=https://cloud.langfuse.com
EOF
```

### Step 4: Verify Connection

```typescript
// TypeScript verification
import { Langfuse } from "langfuse";

const langfuse = new Langfuse({
  publicKey: process.env.LANGFUSE_PUBLIC_KEY,
  secretKey: process.env.LANGFUSE_SECRET_KEY,
  baseUrl: process.env.LANGFUSE_HOST,
});

// Create a test trace
const trace = langfuse.trace({
  name: "connection-test",
  metadata: { test: true },
});

// Flush to ensure data is sent
await langfuse.flushAsync();
console.log("Langfuse connection successful! Check dashboard for trace.");
```

```python
# Python verification
from langfuse import Langfuse
import os

langfuse = Langfuse(
    public_key=os.environ.get("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.environ.get("LANGFUSE_SECRET_KEY"),
    host=os.environ.get("LANGFUSE_HOST"),
)

# Create a test trace
trace = langfuse.trace(name="connection-test", metadata={"test": True})

# Flush to ensure data is sent
langfuse.flush()
print("Langfuse connection successful! Check dashboard for trace.")
```

## Output
- Installed SDK package in node_modules or site-packages
- Environment variables or .env file with API credentials
- Successful connection verification trace visible in dashboard

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Invalid API Key | Incorrect or revoked key | Verify keys in Langfuse dashboard |
| Connection Refused | Wrong host URL | Check LANGFUSE_HOST is correct |
| Network Error | Firewall blocking | Ensure outbound HTTPS to Langfuse host |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |
| 401 Unauthorized | Keys don't match project | Ensure keys are from same project |

## Examples

### TypeScript Initialization with Options
```typescript
import { Langfuse } from "langfuse";

const langfuse = new Langfuse({
  publicKey: process.env.LANGFUSE_PUBLIC_KEY!,
  secretKey: process.env.LANGFUSE_SECRET_KEY!,
  baseUrl: process.env.LANGFUSE_HOST,
  // Optional configuration
  flushAt: 15,        // Flush after 15 events (default: 15)
  flushInterval: 10000, // Flush every 10 seconds (default: 10000ms)  # 10000: 10 seconds in ms
  requestTimeout: 10000, // Request timeout (default: 10000ms)  # 10 seconds in ms
  enabled: process.env.NODE_ENV === "production", // Disable in dev
});

// Ensure clean shutdown
process.on("beforeExit", async () => {
  await langfuse.shutdownAsync();
});
```

### Python Initialization with Options
```python
from langfuse import Langfuse
import os

langfuse = Langfuse(
    public_key=os.environ.get("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.environ.get("LANGFUSE_SECRET_KEY"),
    host=os.environ.get("LANGFUSE_HOST"),
    # Optional configuration
    flush_at=15,           # Flush after 15 events
    flush_interval=10.0,   # Flush every 10 seconds
    enabled=os.environ.get("NODE_ENV") == "production",
)

# Register shutdown handler
import atexit
atexit.register(langfuse.flush)
```

### OpenAI Integration (Automatic Tracing)
```typescript
import { observeOpenAI } from "langfuse";
import OpenAI from "openai";

const openai = observeOpenAI(new OpenAI(), {
  clientInitParams: {
    publicKey: process.env.LANGFUSE_PUBLIC_KEY,
    secretKey: process.env.LANGFUSE_SECRET_KEY,
    baseUrl: process.env.LANGFUSE_HOST,
  },
});

// All OpenAI calls are now automatically traced
const response = await openai.chat.completions.create({
  model: "gpt-4",
  messages: [{ role: "user", content: "Hello!" }],
});
```

## Resources
- [Langfuse Documentation](https://langfuse.com/docs)
- [Langfuse SDK Reference](https://langfuse.com/docs/sdk)
- [Langfuse Cloud Dashboard](https://cloud.langfuse.com)
- [Self-Hosting Guide](https://langfuse.com/docs/deployment/self-host)

## Next Steps
After successful auth, proceed to `langfuse-hello-world` for your first trace.