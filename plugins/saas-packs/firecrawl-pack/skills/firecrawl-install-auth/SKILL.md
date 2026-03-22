---
name: firecrawl-install-auth
description: |
  Install and configure Firecrawl SDK authentication for web scraping.
  Use when setting up a new Firecrawl integration, configuring API keys,
  or initializing Firecrawl in your project.
  Trigger with phrases like "install firecrawl", "setup firecrawl",
  "firecrawl auth", "configure firecrawl API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, firecrawl, api, authentication]

---
# Firecrawl Install & Auth

## Overview
Install the Firecrawl SDK and configure API key authentication. Firecrawl turns any website into LLM-ready markdown or structured data. The SDK is published as `@mendable/firecrawl-js` on npm and `firecrawl-py` on PyPI.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, yarn, or pip)
- Firecrawl API key from [firecrawl.dev/app](https://firecrawl.dev/app) (free tier available)

## Instructions

### Step 1: Install the SDK
```bash
set -euo pipefail
# Node.js (official npm package)
npm install @mendable/firecrawl-js

# Python
pip install firecrawl-py
```

### Step 2: Configure Your API Key
```bash
# Set the environment variable (SDK reads FIRECRAWL_API_KEY automatically)
export FIRECRAWL_API_KEY="fc-YOUR_API_KEY"

# Or add to .env file (use dotenv in your app)
echo 'FIRECRAWL_API_KEY=fc-YOUR_API_KEY' >> .env
```

All Firecrawl API keys start with `fc-`. Get yours at [firecrawl.dev/app](https://firecrawl.dev/app).

### Step 3: Verify Connection — TypeScript
```typescript
import FirecrawlApp from "@mendable/firecrawl-js";

const firecrawl = new FirecrawlApp({
  apiKey: process.env.FIRECRAWL_API_KEY!,
});

// Quick connection test: scrape a simple page
const result = await firecrawl.scrapeUrl("https://example.com", {
  formats: ["markdown"],
});

if (result.success) {
  console.log("Firecrawl connected. Page title:", result.metadata?.title);
  console.log("Content length:", result.markdown?.length, "chars");
} else {
  console.error("Firecrawl error:", result.error);
}
```

### Step 4: Verify Connection — Python
```python
from firecrawl import FirecrawlApp

firecrawl = FirecrawlApp(api_key="fc-YOUR_API_KEY")

# Quick connection test
result = firecrawl.scrape_url("https://example.com", params={
    "formats": ["markdown"]
})

print(f"Title: {result.get('metadata', {}).get('title')}")
print(f"Content: {len(result.get('markdown', ''))} chars")
```

### Step 5: Self-Hosted Setup (Optional)
```typescript
// Point to your own Firecrawl instance instead of api.firecrawl.dev
const firecrawl = new FirecrawlApp({
  apiKey: "any-key",  // required even for self-hosted
  apiUrl: "http://localhost:3002",  // self-hosted Firecrawl URL
});
```

## Output
- `@mendable/firecrawl-js` installed in `node_modules/`
- `FIRECRAWL_API_KEY` environment variable configured
- Successful scrape confirming API connectivity

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid or missing API key | Verify key starts with `fc-` and is set in env |
| `402 Payment Required` | Credits exhausted | Check balance at firecrawl.dev/app |
| `MODULE_NOT_FOUND` | Wrong package name | Use `@mendable/firecrawl-js` not `firecrawl-js` |
| `ECONNREFUSED` | Wrong API URL for self-hosted | Verify `apiUrl` and Docker container is running |
| `429 Too Many Requests` | Rate limit exceeded | Wait for `Retry-After` header duration |

## Examples

### TypeScript with dotenv
```typescript
import "dotenv/config";
import FirecrawlApp from "@mendable/firecrawl-js";

const firecrawl = new FirecrawlApp({
  apiKey: process.env.FIRECRAWL_API_KEY!,
});
```

### Python with Environment Variable
```python
import os
from firecrawl import FirecrawlApp

firecrawl = FirecrawlApp(api_key=os.environ["FIRECRAWL_API_KEY"])
```

### Verify .gitignore Protects Secrets
```bash
set -euo pipefail
# Ensure .env files are gitignored
grep -q "^\.env" .gitignore 2>/dev/null || echo -e "\n.env\n.env.local\n.env.*.local" >> .gitignore
```

## Resources
- [Firecrawl Quickstart](https://docs.firecrawl.dev/introduction)
- [Firecrawl Dashboard](https://firecrawl.dev/app)
- [Node SDK on npm](https://www.npmjs.com/package/@mendable/firecrawl-js)
- [Python SDK on PyPI](https://pypi.org/project/firecrawl-py/)

## Next Steps
After successful auth, proceed to `firecrawl-hello-world` for your first real scrape.
