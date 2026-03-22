---
name: langchain-core-workflow-a
description: |
  Build LangChain LCEL chains with prompts, parsers, and composition.
  Use when creating prompt templates, building RunnableSequence pipelines,
  parallel/branching chains, or multi-step processing workflows.
  Trigger: "langchain chains", "langchain prompts", "LCEL workflow",
  "langchain pipeline", "prompt template", "RunnableSequence".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, langchain, llm, workflow]

---
# LangChain Core Workflow A: Chains & Prompts

## Overview

Build production chains using LCEL (LangChain Expression Language). Covers prompt templates, output parsers, RunnableSequence, RunnableParallel, RunnableBranch, RunnablePassthrough, and chain composition patterns.

## Prerequisites

- `langchain-install-auth` completed
- `@langchain/core` and at least one provider installed

## Prompt Templates

### ChatPromptTemplate

```typescript
import { ChatPromptTemplate, MessagesPlaceholder } from "@langchain/core/prompts";

// Simple template
const simple = ChatPromptTemplate.fromTemplate(
  "Translate '{text}' to {language}"
);

// Multi-message template with chat history slot
const chat = ChatPromptTemplate.fromMessages([
  ["system", "You are a {role}. Respond in {style} style."],
  new MessagesPlaceholder("history"),  // dynamic message injection
  ["human", "{input}"],
]);

// Inspect required variables
console.log(chat.inputVariables);
// ["role", "style", "history", "input"]
```

### Partial Templates

```typescript
// Pre-fill some variables, leave others for later
const partial = await chat.partial({
  role: "senior engineer",
  style: "concise",
});

// Now only needs: history, input
const result = await partial.invoke({
  history: [],
  input: "Explain LCEL",
});
```

## Output Parsers

```typescript
import { StringOutputParser } from "@langchain/core/output_parsers";
import { JsonOutputParser } from "@langchain/core/output_parsers";
import { StructuredOutputParser } from "@langchain/core/output_parsers";
import { z } from "zod";

// String output (most common)
const strParser = new StringOutputParser();

// JSON output with Zod schema
const jsonParser = StructuredOutputParser.fromZodSchema(
  z.object({
    answer: z.string(),
    confidence: z.number(),
    sources: z.array(z.string()),
  })
);

// Get format instructions to inject into prompt
const instructions = jsonParser.getFormatInstructions();
```

## Chain Composition Patterns

### Sequential Chain (RunnableSequence)

```typescript
import { ChatOpenAI } from "@langchain/openai";
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { StringOutputParser } from "@langchain/core/output_parsers";
import { RunnableSequence } from "@langchain/core/runnables";

const model = new ChatOpenAI({ model: "gpt-4o-mini" });

// Extract key points, then summarize
const extractPrompt = ChatPromptTemplate.fromTemplate(
  "Extract 3 key points from:\n{text}"
);
const summarizePrompt = ChatPromptTemplate.fromTemplate(
  "Summarize these points in one sentence:\n{points}"
);

const chain = RunnableSequence.from([
  // Step 1: extract points
  {
    points: extractPrompt
      .pipe(model)
      .pipe(new StringOutputParser()),
  },
  // Step 2: summarize
  summarizePrompt,
  model,
  new StringOutputParser(),
]);

const summary = await chain.invoke({
  text: "Long article text here...",
});
```

### Parallel Execution (RunnableParallel)

```typescript
import { RunnableParallel } from "@langchain/core/runnables";

// Run multiple chains simultaneously on the same input
const analysis = RunnableParallel.from({
  summary: ChatPromptTemplate.fromTemplate("Summarize: {text}")
    .pipe(model)
    .pipe(new StringOutputParser()),

  keywords: ChatPromptTemplate.fromTemplate("Extract 5 keywords from: {text}")
    .pipe(model)
    .pipe(new StringOutputParser()),

  sentiment: ChatPromptTemplate.fromTemplate("Sentiment of: {text}")
    .pipe(model)
    .pipe(new StringOutputParser()),
});

const results = await analysis.invoke({ text: "Your input text" });
// { summary: "...", keywords: "...", sentiment: "..." }
```

### Conditional Branching (RunnableBranch)

```typescript
import { RunnableBranch } from "@langchain/core/runnables";

const technicalChain = ChatPromptTemplate.fromTemplate(
  "Give a technical explanation: {input}"
).pipe(model).pipe(new StringOutputParser());

const simpleChain = ChatPromptTemplate.fromTemplate(
  "Explain like I'm 5: {input}"
).pipe(model).pipe(new StringOutputParser());

const router = RunnableBranch.from([
  [
    (input: { input: string; level: string }) => input.level === "expert",
    technicalChain,
  ],
  // Default fallback
  simpleChain,
]);

const answer = await router.invoke({ input: "What is LCEL?", level: "expert" });
```

### Context Injection (RunnablePassthrough)

```typescript
import { RunnablePassthrough } from "@langchain/core/runnables";

// Pass through original input while adding computed fields
const chain = RunnablePassthrough.assign({
  wordCount: (input: { text: string }) => input.text.split(" ").length,
  uppercase: (input: { text: string }) => input.text.toUpperCase(),
}).pipe(
  ChatPromptTemplate.fromTemplate(
    "The text has {wordCount} words. Summarize: {text}"
  )
).pipe(model).pipe(new StringOutputParser());
```

## Python Equivalent

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableParallel, RunnablePassthrough

llm = ChatOpenAI(model="gpt-4o-mini")

# Sequential: prompt | model | parser
chain = ChatPromptTemplate.from_template("Summarize: {text}") | llm | StrOutputParser()

# Parallel
analysis = RunnableParallel(
    summary=ChatPromptTemplate.from_template("Summarize: {text}") | llm | StrOutputParser(),
    keywords=ChatPromptTemplate.from_template("Keywords: {text}") | llm | StrOutputParser(),
)

# Passthrough with computed fields
chain = (
    RunnablePassthrough.assign(context=lambda x: fetch_context(x["query"]))
    | prompt | llm | StrOutputParser()
)
```

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `Missing value for input` | Template variable not provided | Check `inputVariables` on your prompt |
| `Expected mapping type` | Passing string instead of object | Use `{ input: "text" }` not `"text"` |
| `OutputParserException` | LLM output doesn't match schema | Use `.withStructuredOutput()` instead of manual parsing |
| Parallel timeout | One branch hangs | Add `timeout` to model config |

## Resources

- [LCEL Guide](https://js.langchain.com/docs/concepts/lcel/)
- [RunnableSequence API](https://v03.api.js.langchain.com/classes/_langchain_core.runnables.RunnableSequence.html)
- [Prompt Templates](https://js.langchain.com/docs/concepts/prompt_templates/)

## Next Steps

Proceed to `langchain-core-workflow-b` for agents and tool calling.
