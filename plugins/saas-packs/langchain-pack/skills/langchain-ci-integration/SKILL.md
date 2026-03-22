---
name: langchain-ci-integration
description: |
  Configure CI/CD for LangChain with GitHub Actions, mocked unit tests,
  gated integration tests, and RAG pipeline validation.
  Trigger: "langchain CI", "langchain GitHub Actions",
  "langchain automated tests", "CI langchain", "langchain pipeline testing".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, langchain, testing, ci-cd]

---
# LangChain CI Integration

## Overview

CI/CD pipeline for LangChain applications: mocked unit tests (free, fast), gated integration tests with real LLMs (costs money, slow), RAG pipeline validation, and LangSmith trace integration.

## GitHub Actions Workflow

```yaml
# .github/workflows/langchain-tests.yml
name: LangChain Tests

on:
  pull_request:
    paths: ["src/**", "tests/**", "package.json"]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "20" }
      - run: npm ci
      - name: Unit tests (no API calls)
        run: npx vitest run tests/unit/ --reporter=verbose

  integration-tests:
    runs-on: ubuntu-latest
    if: github.event.pull_request.draft == false
    needs: unit-tests
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "20" }
      - run: npm ci
      - name: Integration tests (real LLM calls)
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          LANGSMITH_TRACING: "true"
          LANGSMITH_API_KEY: ${{ secrets.LANGSMITH_API_KEY }}
          LANGSMITH_PROJECT: "ci-${{ github.run_id }}"
        run: npx vitest run tests/integration/ --reporter=verbose

  typecheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "20" }
      - run: npm ci
      - run: npx tsc --noEmit
```

## Unit Tests: Mocked LLM (Free, Fast)

```typescript
// tests/unit/chains.test.ts
import { describe, it, expect } from "vitest";
import { FakeListChatModel } from "@langchain/core/utils/testing";
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { StringOutputParser } from "@langchain/core/output_parsers";

describe("Summarize Chain", () => {
  const fakeLLM = new FakeListChatModel({
    responses: ["Summary: LangChain enables LLM app development."],
  });

  it("produces output from prompt -> model -> parser", async () => {
    const chain = ChatPromptTemplate.fromTemplate("Summarize: {text}")
      .pipe(fakeLLM)
      .pipe(new StringOutputParser());

    const result = await chain.invoke({ text: "Long document..." });
    expect(result).toContain("LangChain");
  });

  it("passes correct variables to prompt", () => {
    const prompt = ChatPromptTemplate.fromTemplate("Translate {text} to {lang}");
    expect(prompt.inputVariables).toContain("text");
    expect(prompt.inputVariables).toContain("lang");
  });
});
```

## Unit Tests: Tool Validation

```typescript
// tests/unit/tools.test.ts
import { describe, it, expect } from "vitest";
import { calculator, searchTool } from "../../src/tools";

describe("Calculator Tool", () => {
  it("evaluates valid expressions", async () => {
    expect(await calculator.invoke({ expression: "10 * 5" })).toBe("50");
  });

  it("returns error for invalid input", async () => {
    const result = await calculator.invoke({ expression: "abc" });
    expect(result).toContain("Error");
  });

  it("has correct metadata", () => {
    expect(calculator.name).toBe("calculator");
    expect(calculator.description).toBeTruthy();
  });
});
```

## Integration Tests: RAG Pipeline

```typescript
// tests/integration/rag.test.ts
import { describe, it, expect } from "vitest";
import { ChatOpenAI, OpenAIEmbeddings } from "@langchain/openai";
import { MemoryVectorStore } from "langchain/vectorstores/memory";
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { StringOutputParser } from "@langchain/core/output_parsers";
import { RunnableSequence, RunnablePassthrough } from "@langchain/core/runnables";

describe.skipIf(!process.env.OPENAI_API_KEY)("RAG Pipeline", () => {
  it("retrieves relevant documents and answers correctly", async () => {
    const embeddings = new OpenAIEmbeddings({ model: "text-embedding-3-small" });

    const store = await MemoryVectorStore.fromTexts(
      [
        "LangChain was created by Harrison Chase in 2022.",
        "LCEL stands for LangChain Expression Language.",
        "Pinecone is a vector database for AI applications.",
      ],
      [{}, {}, {}],
      embeddings
    );

    const retriever = store.asRetriever({ k: 2 });
    const model = new ChatOpenAI({ model: "gpt-4o-mini", temperature: 0 });

    const prompt = ChatPromptTemplate.fromTemplate(
      "Context: {context}\n\nQuestion: {question}\nAnswer:"
    );

    const chain = RunnableSequence.from([
      {
        context: retriever.pipe((docs) => docs.map((d) => d.pageContent).join("\n")),
        question: new RunnablePassthrough(),
      },
      prompt,
      model,
      new StringOutputParser(),
    ]);

    const answer = await chain.invoke("Who created LangChain?");
    expect(answer.toLowerCase()).toContain("harrison");
  });

  it("handles questions outside context gracefully", async () => {
    // Test that RAG doesn't hallucinate
    const embeddings = new OpenAIEmbeddings({ model: "text-embedding-3-small" });
    const store = await MemoryVectorStore.fromTexts(
      ["TypeScript is maintained by Microsoft."],
      [{}],
      embeddings
    );

    const retriever = store.asRetriever({ k: 1 });
    const model = new ChatOpenAI({ model: "gpt-4o-mini", temperature: 0 });

    const prompt = ChatPromptTemplate.fromTemplate(
      "Based ONLY on this context, answer the question. Say 'I don't know' if not found.\n\nContext: {context}\n\nQuestion: {question}"
    );

    const chain = RunnableSequence.from([
      {
        context: retriever.pipe((docs) => docs.map((d) => d.pageContent).join("\n")),
        question: new RunnablePassthrough(),
      },
      prompt,
      model,
      new StringOutputParser(),
    ]);

    const answer = await chain.invoke("What is the capital of France?");
    expect(answer.toLowerCase()).toMatch(/don.t know|not (in|found)|no information/);
  });
});
```

## Cost Control in CI

```yaml
# Gate integration tests behind PR labels or manual trigger
integration-tests:
  if: |
    github.event.pull_request.draft == false &&
    contains(github.event.pull_request.labels.*.name, 'test:integration')
```

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| Unit tests call real API | Didn't use `FakeListChatModel` | Replace `ChatOpenAI` with fake in tests |
| Integration test missing key | Secret not configured | Add `OPENAI_API_KEY` to repo secrets |
| Flaky RAG test | Embedding variability | Use deterministic data, set `temperature: 0` |
| CI timeout | Model latency | Set `timeout: 15000` on test, use `gpt-4o-mini` |

## Resources

- [LangChain Testing Utils](https://v03.api.js.langchain.com/modules/_langchain_core.utils_testing.html)
- [Vitest Documentation](https://vitest.dev/)
- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions)

## Next Steps

For deployment, see `langchain-deploy-integration`.
