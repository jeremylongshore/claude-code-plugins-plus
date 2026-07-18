---
name: groq-install-auth
description: 'Install and configure Groq SDK authentication for TypeScript or Python.

  Use when setting up a new Groq integration, configuring API keys,

  or initializing the groq-sdk in your project.

  Trigger with phrases like "install groq", "setup groq",

  "groq auth", "configure groq API key".

  '
allowed-tools: Bash(npm:*), Bash(pip:*), Bash(export:*)
version: 1.11.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- groq
- api
- authentication
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# Groq Install & Auth

## Overview

Install the official Groq SDK and configure API key authentication. Groq provides ultra-fast LLM inference on custom LPU hardware through an OpenAI-compatible REST API at `api.groq.com/openai/v1/`.

The workflow is four steps: install the SDK, mint an API key, export it as an
environment variable, and verify the connection by listing models. Each step is
summarized below; deep detail lives in [`references/`](references/).

## Prerequisites

- Node.js 18+ or Python 3.8+
- Package manager (npm, pnpm, or pip)
- Groq account at [console.groq.com](https://console.groq.com)
- API key from GroqCloud console (Settings > API Keys)

## Instructions

### Step 1: Install the SDK

```bash
set -euo pipefail
# TypeScript / JavaScript
npm install groq-sdk

# Python
pip install groq
```

### Step 2: Get Your API Key

1. Go to [console.groq.com/keys](https://console.groq.com/keys)
2. Click "Create API Key"
3. Copy the key (starts with `gsk_`)
4. Store it securely -- you cannot view it again

### Step 3: Configure Environment

Add the [`.gitignore` template](references/configuration.md#gitignore-template)
**before** writing any `.env` file so a key can never be committed:

```bash
# Set environment variable (recommended)
export GROQ_API_KEY="gsk_your_key_here"

# Or create .env file (add .env to .gitignore first)
echo 'GROQ_API_KEY=gsk_your_key_here' >> .env
```

### Step 4: Verify the Connection

Run a short script that lists the models your key can access — a successful list
proves authentication end-to-end. The essential TypeScript skeleton:

```typescript
import Groq from "groq-sdk";

const groq = new Groq({ apiKey: process.env.GROQ_API_KEY });
const models = await groq.models.list();
console.log(models.data.map((m) => m.id));
```

Full runnable TypeScript **and** Python verification scripts, with expected
output: [verification walkthrough](references/verification.md).

## Output

A successful setup produces:

- `groq-sdk` (Node) or `groq` (Python) installed in the project.
- `GROQ_API_KEY` available in the environment (or `.env`, with `.env` gitignored).
- A verification run that prints the accessible models, for example:

```
Connected! Available models:
  llama-3.3-70b-versatile (owned by Meta)
  llama-3.1-8b-instant (owned by Meta)
```

If the verification run prints a `401` instead of a model list, authentication
failed — see [Error Handling](#error-handling).

## SDK Defaults & Key Formats

The SDK auto-reads `GROQ_API_KEY` from the environment when no `apiKey` is passed.
Groq uses a single `gsk_` key type with full API access (no read/write scopes).
Constructor options (`baseURL`, `maxRetries`, `timeout`), the OpenAI-SDK
compatibility path, and the key-format table are in the
[configuration reference](references/configuration.md).

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Invalid API Key` | Key missing, revoked, or mistyped | Verify key at console.groq.com/keys |
| `MODULE_NOT_FOUND groq-sdk` | SDK not installed | Run `npm install groq-sdk` |
| `ModuleNotFoundError: No module named 'groq'` | Python SDK missing | Run `pip install groq` |
| `ENOTFOUND api.groq.com` | Network/DNS issue | Check internet connectivity and firewall |

Extended diagnostics (checking the exported variable, `.env` loading, key
rotation): [troubleshooting reference](references/troubleshooting.md).

## Examples

**Example 1 — Node project from scratch:**

```bash
npm install groq-sdk
export GROQ_API_KEY="gsk_your_key_here"
node --env-file=.env verify.mjs   # lists models → auth confirmed
```

**Example 2 — Python project:**

```bash
pip install groq
export GROQ_API_KEY="gsk_your_key_here"
python verify.py                  # prints accessible models
```

**Example 3 — reuse an existing OpenAI codebase:** point the OpenAI SDK at Groq
by overriding `baseURL` to `https://api.groq.com/openai/v1` and passing your
`gsk_` key. See the [configuration reference](references/configuration.md#sdk-defaults).

Complete, runnable versions of the verification scripts are in the
[verification walkthrough](references/verification.md).

## Resources

- [Groq Quickstart](https://console.groq.com/docs/quickstart)
- [Groq API Reference](https://console.groq.com/docs/api-reference)
- [groq-sdk on npm](https://www.npmjs.com/package/groq-sdk)
- [groq-typescript on GitHub](https://github.com/groq/groq-typescript)

## Next Steps

After successful auth, proceed to the `groq-hello-world` skill to run your first
chat completion. For SDK tuning (retries, timeouts, custom base URL), read the
[configuration reference](references/configuration.md).
