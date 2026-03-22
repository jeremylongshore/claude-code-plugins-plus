---
name: langchain-common-errors
description: |
  Diagnose and fix common LangChain errors and exceptions.
  Use when encountering LangChain import errors, auth failures,
  output parsing issues, agent loops, or version conflicts.
  Trigger: "langchain error", "langchain exception", "debug langchain",
  "langchain not working", "langchain troubleshoot".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, langchain, debugging]

---
# LangChain Common Errors

## Overview

Quick reference for the most frequent LangChain errors with exact error messages, root causes, and copy-paste fixes.

## Import Errors

### `Cannot find module '@langchain/openai'`

```bash
# Provider package not installed
npm install @langchain/openai
# Also: @langchain/anthropic, @langchain/google-genai, @langchain/community
```

### `Cannot import name 'ChatOpenAI' from 'langchain'` (Python)

```python
# Old import path (pre-0.2). Use provider packages:
# OLD: from langchain.chat_models import ChatOpenAI
# NEW:
from langchain_openai import ChatOpenAI
```

### `@langchain/core version mismatch`

```bash
# All @langchain/* packages must share the same minor version
npm ls @langchain/core
# Fix: update all together
npm install @langchain/core@latest @langchain/openai@latest @langchain/anthropic@latest
```

## Authentication Errors

### `AuthenticationError: Incorrect API key provided`

```typescript
// Key not set or wrong format
// Check:
console.log("Key present:", !!process.env.OPENAI_API_KEY);
console.log("Key prefix:", process.env.OPENAI_API_KEY?.slice(0, 7));
// Should be "sk-..." for OpenAI, "sk-ant-..." for Anthropic

// Fix: ensure dotenv is loaded BEFORE imports
import "dotenv/config";
import { ChatOpenAI } from "@langchain/openai";
```

### `Error: OPENAI_API_KEY is not set`

```typescript
// Model constructor can't find the key
// Option 1: environment variable
process.env.OPENAI_API_KEY = "sk-...";

// Option 2: pass directly (not recommended for production)
const model = new ChatOpenAI({
  model: "gpt-4o-mini",
  apiKey: "sk-...",
});
```

## Chain Errors

### `Missing value for input variable "topic"`

```typescript
// Template has variables not provided in invoke()
const prompt = ChatPromptTemplate.fromTemplate("Tell me about {topic} in {language}");
console.log(prompt.inputVariables); // ["topic", "language"]

// Fix: provide ALL variables
await chain.invoke({ topic: "AI", language: "English" }); // not just { topic: "AI" }
```

### `Expected mapping type as input to ChatPromptTemplate`

```typescript
// Passing a string instead of an object
// WRONG:
await chain.invoke("hello");

// RIGHT:
await chain.invoke({ input: "hello" });
```

## Output Parsing Errors

### `OutputParserException: Failed to parse`

```typescript
// LLM output doesn't match expected format
// Fix 1: Use withStructuredOutput (most reliable)
import { z } from "zod";

const schema = z.object({
  answer: z.string(),
  confidence: z.number().optional(), // make fields optional for resilience
});
const structuredModel = model.withStructuredOutput(schema);

// Fix 2: Add retry parser (Python)
// from langchain.output_parsers import RetryWithErrorOutputParser
// retry_parser = RetryWithErrorOutputParser.from_llm(parser=parser, llm=llm)
```

### `ZodError: validation failed`

```typescript
// Structured output doesn't match Zod schema
// Fix: make optional fields nullable, add defaults
const Schema = z.object({
  answer: z.string(),
  confidence: z.number().min(0).max(1).default(0.5),
  sources: z.array(z.string()).default([]),
});
```

## Agent Errors

### `AgentExecutor: max iterations reached`

```typescript
// Agent stuck in a tool-calling loop
const executor = new AgentExecutor({
  agent,
  tools,
  maxIterations: 15,          // increase from default 10
  earlyStoppingMethod: "force", // force stop instead of error
});

// Root cause: usually a vague system prompt. Be specific about when to stop.
```

### `Missing placeholder 'agent_scratchpad'`

```typescript
// Agent prompt MUST include the scratchpad placeholder
const prompt = ChatPromptTemplate.fromMessages([
  ["system", "You are helpful."],
  ["human", "{input}"],
  new MessagesPlaceholder("agent_scratchpad"),  // REQUIRED
]);
```

## Rate Limiting

### `429 Too Many Requests / RateLimitError`

```typescript
// Built-in retry handles this automatically
const model = new ChatOpenAI({
  model: "gpt-4o-mini",
  maxRetries: 5,    // exponential backoff on 429
});

// For batch processing, control concurrency
const results = await chain.batch(inputs, { maxConcurrency: 5 });
```

## Memory/History Errors

### `KeyError: 'chat_history'`

```typescript
// MessagesPlaceholder name must match invoke key
const prompt = ChatPromptTemplate.fromMessages([
  new MessagesPlaceholder("chat_history"),  // this name...
  ["human", "{input}"],
]);

await chain.invoke({
  input: "hello",
  chat_history: [],  // ...must match this key
});
```

## Debugging Toolkit

### Enable Debug Logging

```typescript
// See every step in chain execution
import { setVerbose } from "@langchain/core";
setVerbose(true);  // logs all chain steps

// Python equivalent:
// import langchain; langchain.debug = True
```

### Enable LangSmith Tracing

```bash
# Add to .env — all chains automatically traced
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=lsv2_...
LANGSMITH_PROJECT=my-debug-session
```

### Check Version Compatibility

```bash
# All @langchain/* packages should be on compatible versions
npm ls @langchain/core 2>&1 | head -20

# Python
pip show langchain langchain-core langchain-openai | grep -E "Name|Version"
```

## Quick Diagnostic Script

```typescript
import "dotenv/config";

async function diagnose() {
  const checks: Record<string, string> = {};

  // Check env vars
  checks["OPENAI_API_KEY"] = process.env.OPENAI_API_KEY ? "set" : "MISSING";
  checks["ANTHROPIC_API_KEY"] = process.env.ANTHROPIC_API_KEY ? "set" : "MISSING";

  // Check imports
  try {
    await import("@langchain/core");
    checks["@langchain/core"] = "OK";
  } catch { checks["@langchain/core"] = "MISSING"; }

  try {
    const { ChatOpenAI } = await import("@langchain/openai");
    const llm = new ChatOpenAI({ model: "gpt-4o-mini" });
    await llm.invoke("test");
    checks["OpenAI connection"] = "OK";
  } catch (e: any) {
    checks["OpenAI connection"] = e.message.slice(0, 80);
  }

  console.table(checks);
}

await diagnose();
```

## Resources

- [LangChain Troubleshooting](https://js.langchain.com/docs/troubleshooting/)
- [LangSmith Debugging](https://docs.smith.langchain.com/)
- [GitHub Issues](https://github.com/langchain-ai/langchainjs/issues)

## Next Steps

For complex debugging, use `langchain-debug-bundle` to collect comprehensive evidence.
