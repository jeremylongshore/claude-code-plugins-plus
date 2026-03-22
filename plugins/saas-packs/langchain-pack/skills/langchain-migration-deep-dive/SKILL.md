---
name: langchain-migration-deep-dive
description: |
  Migrate to LangChain from raw OpenAI SDK, LlamaIndex, or custom LLM code.
  Covers codebase assessment, side-by-side validation, RAG migration,
  agent migration, and feature-flagged gradual rollout.
  Trigger: "migrate to langchain", "langchain refactor", "legacy LLM migration",
  "replace openai SDK with langchain", "llamaindex to langchain".
allowed-tools: Read, Write, Edit, Bash(node:*), Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, langchain, llm, migration]

---
# LangChain Migration Deep Dive

## Current State

!`npm list 2>/dev/null | grep -E "openai|langchain|llamaindex" | head -10`

## Overview

Migrate from raw SDK calls (OpenAI, Anthropic) or other frameworks (LlamaIndex, custom agents) to LangChain. Covers codebase scanning, pattern-by-pattern migration, side-by-side validation, and feature-flagged rollout.

## Step 1: Assess Codebase

```typescript
// Scan for migration targets
import * as fs from "fs";
import * as path from "path";

interface MigrationItem {
  file: string;
  line: number;
  pattern: string;
  complexity: "low" | "medium" | "high";
}

function scanForMigration(dir: string): MigrationItem[] {
  const items: MigrationItem[] = [];
  const patterns = [
    { regex: /openai\.chat\.completions\.create/g, name: "OpenAI direct call", complexity: "low" as const },
    { regex: /new OpenAI\(/g, name: "OpenAI SDK init", complexity: "low" as const },
    { regex: /anthropic\.messages\.create/g, name: "Anthropic direct call", complexity: "low" as const },
    { regex: /from llama_index/g, name: "LlamaIndex import", complexity: "medium" as const },
    { regex: /VectorStoreIndex/g, name: "LlamaIndex vector store", complexity: "high" as const },
    { regex: /function_call|tool_choice/g, name: "Manual tool calling", complexity: "high" as const },
  ];

  // Recursive file scan
  function scan(dir: string) {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      if (entry.isDirectory() && !entry.name.startsWith(".") && entry.name !== "node_modules") {
        scan(path.join(dir, entry.name));
      } else if (entry.name.match(/\.(ts|js|py)$/)) {
        const content = fs.readFileSync(path.join(dir, entry.name), "utf-8");
        const lines = content.split("\n");
        for (const p of patterns) {
          lines.forEach((line, i) => {
            if (p.regex.test(line)) {
              items.push({ file: path.join(dir, entry.name), line: i + 1, pattern: p.name, complexity: p.complexity });
            }
            p.regex.lastIndex = 0;
          });
        }
      }
    }
  }

  scan(dir);
  return items;
}
```

## Step 2: Migrate Raw OpenAI SDK to LangChain

### Before (Raw OpenAI SDK)

```typescript
import OpenAI from "openai";

const client = new OpenAI();

async function summarize(text: string) {
  const response = await client.chat.completions.create({
    model: "gpt-4o-mini",
    messages: [
      { role: "system", content: "Summarize the text." },
      { role: "user", content: text },
    ],
    temperature: 0,
  });
  return response.choices[0].message.content;
}
```

### After (LangChain)

```typescript
import { ChatOpenAI } from "@langchain/openai";
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { StringOutputParser } from "@langchain/core/output_parsers";

const summarizeChain = ChatPromptTemplate.fromMessages([
  ["system", "Summarize the text."],
  ["human", "{text}"],
])
  .pipe(new ChatOpenAI({ model: "gpt-4o-mini", temperature: 0 }))
  .pipe(new StringOutputParser());

// Benefits gained:
// - .invoke(), .batch(), .stream() for free
// - Automatic retry with backoff
// - LangSmith tracing
// - .withFallbacks() for provider resilience
// - .withStructuredOutput() for typed results
```

## Step 3: Migrate Manual Function Calling

### Before (Raw Tool Calling)

```typescript
const response = await client.chat.completions.create({
  model: "gpt-4o-mini",
  messages: [{ role: "user", content: input }],
  tools: [{
    type: "function",
    function: {
      name: "search",
      parameters: { type: "object", properties: { query: { type: "string" } } },
    },
  }],
});

// Manual tool call loop
if (response.choices[0].message.tool_calls) {
  for (const tc of response.choices[0].message.tool_calls) {
    const result = await callTool(tc.function.name, JSON.parse(tc.function.arguments));
    // Manually append tool result, re-call API...
  }
}
```

### After (LangChain Agent)

```typescript
import { tool } from "@langchain/core/tools";
import { createToolCallingAgent, AgentExecutor } from "langchain/agents";
import { z } from "zod";

const searchTool = tool(
  async ({ query }) => { /* search logic */ return "results"; },
  { name: "search", description: "Search the web", schema: z.object({ query: z.string() }) }
);

const agent = createToolCallingAgent({ llm, tools: [searchTool], prompt });
const executor = new AgentExecutor({ agent, tools: [searchTool] });

// One call handles the entire tool-calling loop
const result = await executor.invoke({ input: "Search for LangChain news", chat_history: [] });
```

## Step 4: Migrate RAG Pipeline

### Before (Custom RAG)

```typescript
// Manual: embed -> search -> format -> call LLM
const queryEmbed = await openai.embeddings.create({ model: "text-embedding-3-small", input: query });
const results = await pineconeIndex.query({ vector: queryEmbed.data[0].embedding, topK: 5 });
const context = results.matches.map((m) => m.metadata.text).join("\n");
const answer = await openai.chat.completions.create({
  model: "gpt-4o-mini",
  messages: [{ role: "user", content: `Context: ${context}\n\nQuestion: ${query}` }],
});
```

### After (LangChain RAG Chain)

```typescript
import { PineconeStore } from "@langchain/pinecone";
import { OpenAIEmbeddings, ChatOpenAI } from "@langchain/openai";
import { RunnableSequence, RunnablePassthrough } from "@langchain/core/runnables";

const vectorStore = await PineconeStore.fromExistingIndex(
  new OpenAIEmbeddings({ model: "text-embedding-3-small" }),
  { pineconeIndex: index }
);

const ragChain = RunnableSequence.from([
  {
    context: vectorStore.asRetriever({ k: 5 }).pipe(
      (docs) => docs.map((d) => d.pageContent).join("\n")
    ),
    question: new RunnablePassthrough(),
  },
  ragPrompt,
  new ChatOpenAI({ model: "gpt-4o-mini" }),
  new StringOutputParser(),
]);

// Now you get: streaming, batching, tracing, fallbacks for free
```

## Step 5: Side-by-Side Validation

```typescript
async function validateMigration(
  legacyFn: (input: string) => Promise<string>,
  newChain: any,
  testInputs: string[],
) {
  const results = [];

  for (const input of testInputs) {
    const [legacy, migrated] = await Promise.all([
      legacyFn(input),
      newChain.invoke({ input }),
    ]);

    results.push({
      input: input.slice(0, 50),
      legacyLength: legacy.length,
      migratedLength: migrated.length,
      match: legacy.toLowerCase().includes(migrated.toLowerCase().slice(0, 20)),
    });
  }

  console.table(results);
  return results;
}
```

## Step 6: Feature-Flagged Rollout

```typescript
function shouldUseLangChain(userId: string, rolloutPercent: number): boolean {
  // Consistent hashing: same user always gets same experience
  const hash = userId.split("").reduce((acc, c) => acc + c.charCodeAt(0), 0);
  return (hash % 100) < rolloutPercent;
}

async function processRequest(userId: string, input: string) {
  if (shouldUseLangChain(userId, 25)) {  // 25% rollout
    return newChain.invoke({ input });
  }
  return legacySummarize(input);
}

// Gradual rollout: 10% -> 25% -> 50% -> 100%
```

## Migration Checklist

- [ ] Codebase scanned for migration targets
- [ ] Direct SDK calls converted to LCEL chains
- [ ] Manual tool-calling loops replaced with AgentExecutor
- [ ] Custom RAG replaced with LangChain retriever chains
- [ ] Side-by-side validation passing
- [ ] Feature flags configured for gradual rollout
- [ ] LangSmith tracing enabled for monitoring
- [ ] Legacy code removed after 100% rollout

## Error Handling

| Issue | Fix |
|-------|-----|
| Different response format | Add `StringOutputParser` or `.withStructuredOutput()` |
| Missing streaming | Use `.stream()` instead of `.invoke()` |
| Memory format mismatch | Use `RunnableWithMessageHistory` |
| Tool schema differences | Define with Zod, use `tool()` function |

## Resources

- [LangChain.js Migration Guide](https://js.langchain.com/docs/versions/)
- [OpenAI SDK to LangChain](https://js.langchain.com/docs/integrations/chat/openai/)
- [Feature Flags Best Practices](https://launchdarkly.com/blog/best-practices-feature-flags/)

## Next Steps

Use `langchain-upgrade-migration` for LangChain version-to-version upgrades.
