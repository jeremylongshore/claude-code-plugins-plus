---
name: langchain-local-dev-loop
description: |
  Configure LangChain local development workflow with testing and mocks.
  Use when setting up dev environment, creating test fixtures with mocked LLMs,
  or establishing a rapid iteration workflow for LangChain apps.
  Trigger: "langchain dev setup", "langchain local development",
  "langchain testing", "langchain mock", "test langchain chains".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Bash(pytest:*), Bash(python:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, langchain, testing, workflow]

---
# LangChain Local Dev Loop

## Overview

Set up a productive local development workflow for LangChain: project structure, mocked LLMs for unit tests (no API calls), integration tests with real providers, and dev tooling.

## Project Structure

```
my-langchain-app/
├── src/
│   ├── chains/           # LCEL chain definitions
│   │   ├── summarize.ts
│   │   └── rag.ts
│   ├── tools/            # Tool definitions
│   │   └── calculator.ts
│   ├── agents/           # Agent configurations
│   │   └── assistant.ts
│   └── index.ts
├── tests/
│   ├── unit/             # Mocked tests (no API calls)
│   │   └── chains.test.ts
│   └── integration/      # Real API tests (CI gated)
│       └── rag.test.ts
├── .env                  # API keys (git-ignored)
├── .env.example          # Template for required vars
├── package.json
├── tsconfig.json
└── vitest.config.ts
```

## Step 1: Dev Dependencies

```bash
set -euo pipefail
npm install @langchain/core @langchain/openai langchain zod
npm install -D vitest @types/node tsx dotenv typescript
```

## Step 2: Vitest Configuration

```typescript
// vitest.config.ts
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    include: ["tests/**/*.test.ts"],
    environment: "node",
    setupFiles: ["./tests/setup.ts"],
    testTimeout: 30000,
  },
});
```

```typescript
// tests/setup.ts
import "dotenv/config";
```

## Step 3: Unit Tests with Mocked LLM

```typescript
// tests/unit/chains.test.ts
import { describe, it, expect, vi } from "vitest";
import { FakeListChatModel } from "@langchain/core/utils/testing";
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { StringOutputParser } from "@langchain/core/output_parsers";

describe("Summarize Chain", () => {
  it("processes input through prompt -> model -> parser", async () => {
    // FakeListChatModel returns predefined responses (no API call)
    const fakeLLM = new FakeListChatModel({
      responses: ["This is a summary of the document."],
    });

    const prompt = ChatPromptTemplate.fromTemplate("Summarize: {text}");
    const chain = prompt.pipe(fakeLLM).pipe(new StringOutputParser());

    const result = await chain.invoke({ text: "Long document text..." });
    expect(result).toBe("This is a summary of the document.");
  });

  it("handles structured output", async () => {
    const fakeLLM = new FakeListChatModel({
      responses: ['{"sentiment": "positive", "score": 0.95}'],
    });

    const prompt = ChatPromptTemplate.fromTemplate("Analyze: {text}");
    const chain = prompt.pipe(fakeLLM).pipe(new StringOutputParser());

    const result = await chain.invoke({ text: "Great product!" });
    const parsed = JSON.parse(result);
    expect(parsed.sentiment).toBe("positive");
    expect(parsed.score).toBeGreaterThan(0.5);
  });

  it("chain has correct input variables", () => {
    const prompt = ChatPromptTemplate.fromTemplate(
      "Translate {text} to {language}"
    );
    expect(prompt.inputVariables).toEqual(["text", "language"]);
  });
});
```

## Step 4: Tool Unit Tests

```typescript
// tests/unit/tools.test.ts
import { describe, it, expect } from "vitest";
import { tool } from "@langchain/core/tools";
import { z } from "zod";

const calculator = tool(
  async ({ expression }) => {
    try {
      return String(Function(`"use strict"; return (${expression})`)());
    } catch {
      return "Error: invalid expression";
    }
  },
  {
    name: "calculator",
    description: "Evaluate math",
    schema: z.object({ expression: z.string() }),
  }
);

describe("Calculator Tool", () => {
  it("evaluates valid expressions", async () => {
    const result = await calculator.invoke({ expression: "2 + 2" });
    expect(result).toBe("4");
  });

  it("handles invalid input gracefully", async () => {
    const result = await calculator.invoke({ expression: "not math" });
    expect(result).toContain("Error");
  });

  it("has correct schema", () => {
    expect(calculator.name).toBe("calculator");
    expect(calculator.description).toBe("Evaluate math");
  });
});
```

## Step 5: Integration Tests (Real API)

```typescript
// tests/integration/rag.test.ts
import { describe, it, expect } from "vitest";
import { ChatOpenAI, OpenAIEmbeddings } from "@langchain/openai";
import { MemoryVectorStore } from "langchain/vectorstores/memory";

describe.skipIf(!process.env.OPENAI_API_KEY)("RAG Integration", () => {
  it("retrieves relevant documents", async () => {
    const embeddings = new OpenAIEmbeddings({ model: "text-embedding-3-small" });

    const store = await MemoryVectorStore.fromTexts(
      [
        "LangChain is a framework for building LLM applications.",
        "TypeScript is a typed superset of JavaScript.",
        "Python is a popular programming language.",
      ],
      [{}, {}, {}],
      embeddings
    );

    const results = await store.similaritySearch("LLM framework", 1);
    expect(results[0].pageContent).toContain("LangChain");
  });

  it("model responds to prompts", async () => {
    const model = new ChatOpenAI({ model: "gpt-4o-mini", temperature: 0 });
    const response = await model.invoke("Say exactly: test passed");
    expect(response.content).toContain("test passed");
  });
});
```

## Step 6: Package Scripts

```json
{
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "test": "vitest run tests/unit/",
    "test:watch": "vitest tests/unit/",
    "test:integration": "vitest run tests/integration/",
    "test:all": "vitest run",
    "typecheck": "tsc --noEmit",
    "lint": "eslint src/ tests/"
  }
}
```

## Dev Workflow

```bash
# Rapid iteration (no API costs)
npm test                      # Run unit tests with mocked LLMs
npm run test:watch            # Watch mode for TDD

# Validate with real APIs (costs money)
npm run test:integration      # Needs OPENAI_API_KEY

# Type safety
npm run typecheck
```

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `Cannot find module` | Missing dependency | `npm install @langchain/core` |
| `FakeListChatModel` not found | Old version | Update `@langchain/core` to latest |
| Integration test hangs | No API key | Tests use `describe.skipIf` to skip gracefully |
| `ERR_REQUIRE_ESM` | CJS/ESM mismatch | Add `"type": "module"` to package.json |

## Resources

- [Vitest Documentation](https://vitest.dev/)
- [LangChain Testing Utils](https://v03.api.js.langchain.com/modules/_langchain_core.utils_testing.html)
- [FakeListChatModel API](https://v03.api.js.langchain.com/classes/_langchain_core.utils_testing.FakeListChatModel.html)

## Next Steps

Proceed to `langchain-sdk-patterns` for production-ready code patterns.
