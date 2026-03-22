---
name: langchain-upgrade-migration
description: |
  Upgrade LangChain SDK versions safely with import path migration,
  LCEL conversion from legacy chains, and agent API updates.
  Trigger: "upgrade langchain", "langchain migration", "langchain breaking changes",
  "update langchain version", "langchain 0.3", "langchain deprecation".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, langchain, migration]

---
# LangChain Upgrade Migration

## Current State

!`npm list @langchain/core @langchain/openai 2>/dev/null | head -10`

## Overview

Safely upgrade LangChain versions: check compatibility, migrate import paths, convert legacy chains to LCEL, update agent APIs, and validate with tests.

## Breaking Changes Timeline

### 0.1.x to 0.2.x (Major Restructuring)

- `@langchain/core` extracted as separate package
- Chat models moved to provider packages (`@langchain/openai`, `@langchain/anthropic`)
- Imports changed from `langchain/*` to `@langchain/core/*`

### 0.2.x to 0.3.x (LCEL Standardization)

- Legacy `LLMChain`, `ConversationChain` deprecated
- `initialize_agent` deprecated (use `createToolCallingAgent`)
- Memory API: `ConversationBufferMemory` replaced by `RunnableWithMessageHistory`
- All chains should use LCEL pipe syntax

## Step 1: Check Current Versions

```bash
# Node.js
npm ls @langchain/core @langchain/openai langchain 2>&1 | head -20

# Python
pip show langchain langchain-core langchain-openai | grep -E "Name|Version"
```

## Step 2: Migrate Import Paths (TypeScript)

```typescript
// OLD (pre-0.2)
import { ChatOpenAI } from "langchain/chat_models/openai";
import { PromptTemplate } from "langchain/prompts";
import { LLMChain } from "langchain/chains";
import { BufferMemory } from "langchain/memory";

// NEW (0.3+)
import { ChatOpenAI } from "@langchain/openai";
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { StringOutputParser } from "@langchain/core/output_parsers";
// LLMChain replaced by LCEL: prompt.pipe(model).pipe(parser)
```

```python
# OLD (pre-0.2)
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain

# NEW (0.3+)
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
```

## Step 3: Convert LLMChain to LCEL

```typescript
// OLD: LLMChain (deprecated)
import { LLMChain } from "langchain/chains";
const chain = new LLMChain({ llm, prompt });
const result = await chain.call({ input: "hello" });

// NEW: LCEL pipe syntax
import { StringOutputParser } from "@langchain/core/output_parsers";
const chain = prompt.pipe(model).pipe(new StringOutputParser());
const result = await chain.invoke({ input: "hello" });
```

```python
# OLD
from langchain.chains import LLMChain
chain = LLMChain(llm=llm, prompt=prompt)
result = chain.run(input="hello")

# NEW
chain = prompt | llm | StrOutputParser()
result = chain.invoke({"input": "hello"})
```

## Step 4: Migrate Agents

```typescript
// OLD: initialize_agent (deprecated)
import { initializeAgentExecutorWithOptions } from "langchain/agents";
const executor = await initializeAgentExecutorWithOptions(tools, llm, {
  agentType: "chat-conversational-react-description",
});

// NEW: createToolCallingAgent
import { createToolCallingAgent, AgentExecutor } from "langchain/agents";
import { ChatPromptTemplate, MessagesPlaceholder } from "@langchain/core/prompts";

const prompt = ChatPromptTemplate.fromMessages([
  ["system", "You are a helpful assistant."],
  new MessagesPlaceholder("chat_history"),
  ["human", "{input}"],
  new MessagesPlaceholder("agent_scratchpad"),
]);

const agent = createToolCallingAgent({ llm, tools, prompt });
const executor = new AgentExecutor({ agent, tools });
```

## Step 5: Migrate Memory

```typescript
// OLD: BufferMemory (deprecated)
import { BufferMemory } from "langchain/memory";
const memory = new BufferMemory();
const chain = new ConversationChain({ llm, memory });

// NEW: RunnableWithMessageHistory
import { RunnableWithMessageHistory } from "@langchain/core/runnables";
import { ChatMessageHistory } from "@langchain/community/stores/message/in_memory";

const store = new Map<string, ChatMessageHistory>();

function getHistory(sessionId: string) {
  if (!store.has(sessionId)) store.set(sessionId, new ChatMessageHistory());
  return store.get(sessionId)!;
}

const chainWithHistory = new RunnableWithMessageHistory({
  runnable: chain,
  getMessageHistory: getHistory,
  inputMessagesKey: "input",
  historyMessagesKey: "history",
});

await chainWithHistory.invoke(
  { input: "Hello" },
  { configurable: { sessionId: "user-1" } }
);
```

## Step 6: Upgrade Packages

```bash
# Node.js — update all @langchain/* together
npm install @langchain/core@latest @langchain/openai@latest langchain@latest

# Verify no version conflicts
npm ls @langchain/core

# Python
pip install --upgrade langchain langchain-core langchain-openai langchain-community
pip show langchain langchain-core | grep Version
```

## Step 7: Run Tests and Check Deprecations

```bash
# TypeScript
npx vitest run
npx tsc --noEmit

# Python — check for deprecation warnings
pytest tests/ -W error::DeprecationWarning -v
```

## Migration Checklist

- [ ] Current versions documented
- [ ] Breaking changes reviewed for your version jump
- [ ] All `langchain/*` imports updated to `@langchain/core/*` or provider packages
- [ ] `LLMChain` replaced with LCEL `.pipe()` chains
- [ ] `initializeAgent` replaced with `createToolCallingAgent`
- [ ] `BufferMemory` replaced with `RunnableWithMessageHistory`
- [ ] All `@langchain/*` packages on compatible versions
- [ ] Tests passing
- [ ] No deprecation warnings
- [ ] Staging validation complete

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `Cannot find module` | Old import path | Update to `@langchain/core/*` or provider package |
| `LLMChain is not a constructor` | Removed in 0.3+ | Convert to LCEL |
| `DeprecationWarning` | Using old API | Follow migration guide for replacement |
| Version conflict | Mixed `@langchain/*` versions | Update all packages together |

## Resources

- [LangChain.js Migration Guide](https://js.langchain.com/docs/versions/)
- [Python Migration Guide](https://python.langchain.com/docs/versions/migrating_chains/)
- [Release Notes](https://github.com/langchain-ai/langchainjs/releases)

## Next Steps

After upgrade, use `langchain-common-errors` to troubleshoot any issues.
