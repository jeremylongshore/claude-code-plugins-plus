---
name: runway-install-auth
description: |
  Runway install auth — AI video generation and creative AI platform.
  Use when working with Runway for video generation, image editing, or creative AI.
  Trigger with phrases like "runway install auth", "runway-install-auth", "AI video generation".
allowed-tools: Read, Write, Edit, Bash(pip:*), Bash(npm:*), Bash(curl:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, runway, ai, video-generation, creative]
compatible-with: claude-code, codex, openclaw
---

# Runway Install Auth

## Overview
Install the Runway ML SDK and configure API key authentication for AI video generation.

## Prerequisites
- Runway account at runwayml.com
- API key from the Runway Developer Portal (dev.runwayml.com)
- Python 3.9+ or Node.js 18+

## Instructions

### Step 1: Install SDK
```bash
set -euo pipefail
# Python
pip install runwayml

# Node.js
npm install @runwayml/sdk
```

### Step 2: Configure Environment
```bash
# .env
RUNWAYML_API_SECRET=key_xxxxxxxxxxxxxxxxxxxxxxxx
```

### Step 3: Verify Connection (Python)
```python
from runwayml import RunwayML

client = RunwayML()  # Reads RUNWAYML_API_SECRET from env

# The client is ready — no explicit auth call needed
# SDK auto-authenticates on first API call
print("RunwayML client initialized")
```

### Step 4: Verify Connection (Node.js)
```typescript
import RunwayML from '@runwayml/sdk';

const runway = new RunwayML();  // Reads RUNWAYML_API_SECRET from env
console.log('RunwayML client initialized');
```

## Output
- `runwayml` SDK installed
- API key configured via environment variable
- Client ready for video generation

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid API key | Verify key at dev.runwayml.com |
| `ModuleNotFoundError` | SDK not installed | `pip install runwayml` |
| `RUNWAYML_API_SECRET not set` | Missing env var | Set in .env or export |

## Resources
- [Runway API Documentation](https://docs.dev.runwayml.com/)
- [Python SDK](https://github.com/runwayml/sdk-python)
- [API Getting Started](https://docs.dev.runwayml.com/guides/using-the-api/)

## Next Steps
Generate your first video: `runway-hello-world`
