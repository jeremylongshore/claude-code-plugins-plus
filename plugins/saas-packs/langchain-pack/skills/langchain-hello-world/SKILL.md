---
name: langchain-hello-world
description: |
  Create a minimal working LangChain example with LCEL chains.
  Use when starting a new LangChain integration, testing your setup,
  or learning LCEL pipe syntax with prompts and output parsers.
  Trigger: "langchain hello world", "langchain example",
  "langchain quick start", "simple langchain code", "first langchain app".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, langchain, testing]

---
# LangChain Hello World

## Overview

Minimal working examples demonstrating LCEL (LangChain Expression Language) -- the `.pipe()` chain syntax that is the foundation of all LangChain applications.

## Prerequisites

- Completed `langchain-install-auth` setup
- Valid LLM provider API key configured

## Example 1: Simplest Chain (TypeScript)

```typescript
import { ChatOpenAI } from "@langchain/openai";
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { StringOutputParser } from "@langchain/core/output_parsers";

// Three components: prompt -> model -> parser
const prompt = ChatPromptTemplate.fromTemplate("Tell me a joke about {topic}");
const model = new ChatOpenAI({ model: "gpt-4o-mini" });
const parser = new StringOutputParser();

// LCEL: chain them with .pipe()
const chain = prompt.pipe(model).pipe(parser);

const result = await chain.invoke({ topic: "TypeScript" });
console.log(result);
// "Why do TypeScript developers wear glasses? Because they can't C#!"
```

## Example 2: Chat with System Prompt

```typescript
import { ChatOpenAI } from "@langchain/openai";
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { StringOutputParser } from "@langchain/core/output_parsers";

const prompt = ChatPromptTemplate.fromMessages([
  ["system", "You are a {persona}. Keep answers under 50 words."],
  ["human", "{question}"],
]);

const chain = prompt
  .pipe(new ChatOpenAI({ model: "gpt-4o-mini" }))
  .pipe(new StringOutputParser());

const answer = await chain.invoke({
  persona: "senior DevOps engineer",
  question: "What is the most important Kubernetes concept?",
});
console.log(answer);
```

## Example 3: Structured Output with Zod

```typescript
import { ChatOpenAI } from "@langchain/openai";
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { z } from "zod";

const ReviewSchema = z.object({
  sentiment: z.enum(["positive", "negative", "neutral"]),
  confidence: z.number().min(0).max(1),
  summary: z.string().describe("One-sentence summary"),
});

const model = new ChatOpenAI({ model: "gpt-4o-mini" });
const structuredModel = model.withStructuredOutput(ReviewSchema);

const prompt = ChatPromptTemplate.fromTemplate(
  "Analyze the sentiment of this review:\n\n{review}"
);

const chain = prompt.pipe(structuredModel);

const result = await chain.invoke({
  review: "LangChain makes building AI apps surprisingly straightforward.",
});
console.log(result);
// { sentiment: "positive", confidence: 0.92, summary: "..." }
```

## Example 4: Streaming

```typescript
import { ChatOpenAI } from "@langchain/openai";
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { StringOutputParser } from "@langchain/core/output_parsers";

const chain = ChatPromptTemplate.fromTemplate("Write a haiku about {topic}")
  .pipe(new ChatOpenAI({ model: "gpt-4o-mini" }))
  .pipe(new StringOutputParser());

// Stream tokens as they arrive
const stream = await chain.stream({ topic: "coding" });
for await (const chunk of stream) {
  process.stdout.write(chunk);
}
```

## Example 5: Python Equivalent

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

prompt = ChatPromptTemplate.from_template("Tell me about {topic}")
model = ChatOpenAI(model="gpt-4o-mini")
parser = StrOutputParser()

# LCEL uses | operator in Python
chain = prompt | model | parser

result = chain.invoke({"topic": "LangChain"})
print(result)
```

## How LCEL Works

Every component in an LCEL chain implements the `Runnable` interface:

| Method | Purpose |
|--------|---------|
| `.invoke(input)` | Single input, single output |
| `.batch(inputs)` | Process array of inputs |
| `.stream(input)` | Yield output chunks |
| `.pipe(next)` | Chain to next runnable |

The `.pipe()` method (or `|` in Python) creates a `RunnableSequence` where each step's output feeds the next step's input. Every LangChain component -- prompts, models, parsers, retrievers -- is a Runnable.

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `Missing value for input topic` | Template variable not in invoke args | Match `invoke({})` keys to template `{variables}` |
| `Cannot read properties of undefined` | Chain not awaited | Add `await` before `.invoke()` |
| `Rate limit reached` | Too many API calls | Add delay or use `gpt-4o-mini` for testing |

## Resources

- [LCEL Conceptual Guide](https://js.langchain.com/docs/concepts/lcel/)
- [Prompt Templates](https://js.langchain.com/docs/concepts/prompt_templates/)
- [Output Parsers](https://js.langchain.com/docs/concepts/output_parsers/)

## Next Steps

Proceed to `langchain-core-workflow-a` for advanced chain composition.
