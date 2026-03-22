---
name: langchain-install-auth
description: |
  Install and configure LangChain SDK with provider authentication.
  Use when setting up a new LangChain project, configuring API keys
  for OpenAI/Anthropic/Google, or initializing @langchain/core in Node.js or Python.
  Trigger: "install langchain", "setup langchain", "langchain auth",
  "configure langchain API key", "langchain credentials".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Bash(pnpm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, langchain, api, authentication]

---
# LangChain Install & Auth

## Overview

Set up LangChain SDK packages and configure provider authentication. Covers the modular `@langchain/*` package ecosystem for Node.js/TypeScript and `langchain-*` packages for Python.

## Prerequisites

- Node.js 18+ or Python 3.9+
- Package manager (npm/pnpm or pip/poetry)
- API key from at least one LLM provider (OpenAI, Anthropic, Google)

## Instructions

### Step 1: Install Core Packages (TypeScript)

```bash
set -euo pipefail
# Core + one provider (pick what you need)
npm install @langchain/core @langchain/openai

# Additional providers
npm install @langchain/anthropic          # Claude models
npm install @langchain/google-genai       # Gemini models
npm install @langchain/community          # 100+ community integrations

# Common companions
npm install @langchain/textsplitters      # Text chunking for RAG
npm install @langchain/pinecone           # Pinecone vector store
npm install zod                           # Schema validation (structured output)
```

### Step 2: Install Core Packages (Python)

```bash
set -euo pipefail
pip install langchain langchain-core

# Provider packages (install only what you need)
pip install langchain-openai              # ChatOpenAI, OpenAIEmbeddings
pip install langchain-anthropic           # ChatAnthropic
pip install langchain-google-genai        # ChatGoogleGenerativeAI
pip install langchain-community           # Community integrations
```

### Step 3: Configure Authentication

```bash
# Create .env file (add to .gitignore!)
cat > .env << 'ENVEOF'
# OpenAI — https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-...

# Anthropic — https://console.anthropic.com/
ANTHROPIC_API_KEY=sk-ant-...

# Google — https://aistudio.google.com/apikey
GOOGLE_API_KEY=AI...

# LangSmith (optional but recommended) — https://smith.langchain.com
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=lsv2_...
LANGSMITH_PROJECT=my-project
ENVEOF

echo '.env' >> .gitignore
```

### Step 4: Verify Connection (TypeScript)

```typescript
import { ChatOpenAI } from "@langchain/openai";
import { ChatAnthropic } from "@langchain/anthropic";
import "dotenv/config";

// OpenAI
const openai = new ChatOpenAI({ model: "gpt-4o-mini", temperature: 0 });
const res1 = await openai.invoke("Say 'OpenAI connected'");
console.log("OpenAI:", res1.content);

// Anthropic
const anthropic = new ChatAnthropic({ model: "claude-sonnet-4-20250514" });
const res2 = await anthropic.invoke("Say 'Anthropic connected'");
console.log("Anthropic:", res2.content);
```

### Step 5: Verify Connection (Python)

```python
import os
from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

# OpenAI
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
print(llm.invoke("Say 'connected'").content)

# Anthropic
llm2 = ChatAnthropic(model="claude-sonnet-4-20250514")
print(llm2.invoke("Say 'connected'").content)
```

## Package Architecture

```
@langchain/core          # Base abstractions: Runnables, prompts, output parsers
  ├── @langchain/openai  # ChatOpenAI, OpenAIEmbeddings
  ├── @langchain/anthropic  # ChatAnthropic
  ├── @langchain/google-genai  # ChatGoogleGenerativeAI
  ├── @langchain/community  # 100+ integrations
  ├── @langchain/pinecone   # PineconeStore
  ├── @langchain/textsplitters  # RecursiveCharacterTextSplitter
  └── langchain             # High-level: agents, chains, tools
```

Every `@langchain/*` package depends on `@langchain/core`. You never import from `langchain` directly for base types -- always use `@langchain/core` for prompts, output parsers, messages, and runnables.

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `Cannot find module '@langchain/openai'` | Package not installed | `npm install @langchain/openai` |
| `AuthenticationError: Incorrect API key` | Invalid or missing key | Check `.env` and `dotenv/config` import |
| `Could not import @langchain/core` | Version mismatch | Ensure all `@langchain/*` packages share same minor version |
| `RateLimitError` | Quota exceeded | Check provider dashboard, implement backoff |
| `ENOTFOUND api.openai.com` | Network blocked | Check firewall/proxy settings |

## Troubleshooting Version Conflicts

```bash
# Check installed versions (all should share same minor)
npm ls @langchain/core

# Fix version conflicts
npm install @langchain/core@latest @langchain/openai@latest @langchain/anthropic@latest
```

## Resources

- [LangChain.js Docs](https://js.langchain.com/docs/)
- [LangChain Python Docs](https://python.langchain.com/docs/)
- [OpenAI API Keys](https://platform.openai.com/api-keys)
- [Anthropic Console](https://console.anthropic.com/)
- [LangSmith](https://smith.langchain.com)

## Next Steps

After successful auth, proceed to `langchain-hello-world` for your first chain.
