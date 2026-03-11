---
name: langchain-install-auth
description: |
  Install and configure LangChain SDK/CLI authentication.
  Use when setting up a new LangChain integration, configuring API keys,
  or initializing LangChain in your project.
  Trigger with phrases like "install langchain", "setup langchain",
  "langchain auth", "configure langchain API key", "langchain credentials".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# LangChain Install & Auth

## Overview
Set up LangChain SDK and configure LLM provider authentication credentials.

## Prerequisites
- Python 3.9+ or Node.js 18+
- Package manager (pip, poetry, or npm)
- LLM provider account (OpenAI, Anthropic, Google, etc.)
- API key from your LLM provider dashboard

## Instructions

### Step 1: Install LangChain Core
```bash
set -euo pipefail
# Python (recommended)
pip install langchain langchain-core langchain-community

# Or with specific providers
pip install langchain-openai langchain-anthropic langchain-google-genai

# Node.js
npm install langchain @langchain/core @langchain/community
```

### Step 2: Configure Authentication
```bash
# OpenAI
export OPENAI_API_KEY="your-openai-key"

# Anthropic
export ANTHROPIC_API_KEY="your-anthropic-key"

# Google
export GOOGLE_API_KEY="your-google-key"

# Or create .env file
echo 'OPENAI_API_KEY=your-openai-key' >> .env
```

### Step 3: Verify Connection
```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini")
response = llm.invoke("Say hello!")
print(response.content)
```

## Output
- Installed LangChain packages in virtual environment
- Environment variables or .env file with API keys
- Successful connection verification output

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Invalid API Key | Incorrect or expired key | Verify key in provider dashboard |
| Rate Limited | Exceeded quota | Check quota limits, implement backoff |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `pip install` again, check Python version |
| Provider Error | Service unavailable | Check provider status page |

## Examples

### Python Setup (OpenAI)
```python
import os
from langchain_openai import ChatOpenAI

# Ensure API key is set
assert os.environ.get("OPENAI_API_KEY"), "Set OPENAI_API_KEY"

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.7,
    max_tokens=1000  # 1000: 1 second in ms
)
```

### Python Setup (Anthropic)
```python
from langchain_anthropic import ChatAnthropic

llm = ChatAnthropic(
    model="claude-3-5-sonnet-20241022",  # 20241022 = date/version stamp
    temperature=0.7
)
```

### TypeScript Setup
```typescript
import { ChatOpenAI } from "@langchain/openai";

const llm = new ChatOpenAI({
  modelName: "gpt-4o-mini",
  temperature: 0.7
});
```

## Resources
- [LangChain Documentation](https://python.langchain.com/docs/)
- [LangChain JS/TS](https://js.langchain.com/docs/)
- [OpenAI API Keys](https://platform.openai.com/api-keys)
- [Anthropic Console](https://console.anthropic.com/)

## Next Steps
After successful auth, proceed to `langchain-hello-world` for your first chain.