---
name: langchain-reference-architecture
description: |
  Implement LangChain reference architecture for production systems:
  layered design, provider abstraction, chain registry, RAG pipelines,
  and multi-agent orchestration.
  Trigger: "langchain architecture", "langchain design patterns",
  "langchain scalable", "langchain enterprise", "LLM architecture".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, langchain, llm, scaling]

---
# LangChain Reference Architecture

## Overview

Production architectural patterns for LangChain: layered project structure, provider abstraction for vendor flexibility, chain registry for dynamic management, RAG architecture, and multi-agent orchestration.

## Layered Architecture

```
src/
├── api/                    # HTTP layer (Express/Fastify/FastAPI)
│   ├── routes/
│   │   ├── chat.ts         # POST /api/chat, /api/chat/stream
│   │   └── documents.ts    # POST /api/documents/ingest
│   └── middleware/
│       ├── auth.ts         # JWT/OAuth validation
│       └── rateLimit.ts    # Per-user rate limiting
├── core/                   # Business logic (pure, testable)
│   ├── chains/
│   │   ├── summarize.ts    # Summarize chain factory
│   │   ├── qa.ts           # Q&A chain factory
│   │   └── rag.ts          # RAG chain factory
│   ├── agents/
│   │   └── assistant.ts    # Agent with tools
│   └── tools/
│       ├── calculator.ts
│       └── search.ts
├── infra/                  # External integrations
│   ├── llm/
│   │   └── factory.ts      # LLM provider factory
│   ├── vectorStore/
│   │   └── pinecone.ts     # Vector store setup
│   └── cache/
│       └── redis.ts        # Response caching
├── config/
│   ├── index.ts            # Config loader + validation
│   └── models.ts           # Model configurations
└── index.ts                # App entry point
```

## Provider Abstraction (LLM Factory)

```typescript
// src/infra/llm/factory.ts
import { ChatOpenAI } from "@langchain/openai";
import { ChatAnthropic } from "@langchain/anthropic";
import { BaseChatModel } from "@langchain/core/language_models/chat_models";

type Provider = "openai" | "anthropic";

interface ModelConfig {
  provider: Provider;
  model: string;
  temperature?: number;
  maxRetries?: number;
  timeout?: number;
}

const DEFAULT_CONFIG: Partial<ModelConfig> = {
  temperature: 0,
  maxRetries: 3,
  timeout: 30000,
};

export function createModel(config: ModelConfig): BaseChatModel {
  const merged = { ...DEFAULT_CONFIG, ...config };

  switch (merged.provider) {
    case "openai":
      return new ChatOpenAI({
        model: merged.model,
        temperature: merged.temperature,
        maxRetries: merged.maxRetries,
        timeout: merged.timeout,
      });

    case "anthropic":
      return new ChatAnthropic({
        model: merged.model,
        temperature: merged.temperature,
        maxRetries: merged.maxRetries,
      });

    default:
      throw new Error(`Unknown provider: ${merged.provider}`);
  }
}

// Usage: swap providers without touching chain code
const model = createModel({
  provider: "openai",
  model: "gpt-4o-mini",
});
```

## Chain Registry

```typescript
// src/core/chains/registry.ts
import { Runnable } from "@langchain/core/runnables";

class ChainRegistry {
  private chains = new Map<string, Runnable>();

  register(name: string, chain: Runnable) {
    this.chains.set(name, chain);
  }

  get(name: string): Runnable {
    const chain = this.chains.get(name);
    if (!chain) throw new Error(`Chain not found: ${name}`);
    return chain;
  }

  list(): string[] {
    return Array.from(this.chains.keys());
  }
}

export const registry = new ChainRegistry();

// At startup:
registry.register("summarize", summarizeChain);
registry.register("qa", qaChain);
registry.register("rag", ragChain);

// In API routes:
app.post("/api/chain/:name/invoke", async (req, res) => {
  const chain = registry.get(req.params.name);
  const result = await chain.invoke(req.body.input);
  res.json({ result });
});
```

## RAG Architecture

```typescript
// src/core/chains/rag.ts
import { ChatOpenAI, OpenAIEmbeddings } from "@langchain/openai";
import { PineconeStore } from "@langchain/pinecone";
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { StringOutputParser } from "@langchain/core/output_parsers";
import { RunnableSequence, RunnablePassthrough } from "@langchain/core/runnables";

export function createRAGChain(vectorStore: PineconeStore) {
  const retriever = vectorStore.asRetriever({ k: 4 });
  const model = new ChatOpenAI({ model: "gpt-4o-mini", temperature: 0 });

  const prompt = ChatPromptTemplate.fromTemplate(`
Answer based only on the provided context.
If the answer is not in the context, say "I don't have that information."

Context:
{context}

Question: {question}`);

  return RunnableSequence.from([
    {
      context: retriever.pipe(
        (docs) => docs.map((d: any) => d.pageContent).join("\n\n")
      ),
      question: new RunnablePassthrough(),
    },
    prompt,
    model,
    new StringOutputParser(),
  ]);
}
```

## Multi-Agent Orchestration

```typescript
// src/core/agents/orchestrator.ts
import { ChatOpenAI } from "@langchain/openai";
import { createToolCallingAgent, AgentExecutor } from "langchain/agents";
import { ChatPromptTemplate, MessagesPlaceholder } from "@langchain/core/prompts";

interface SpecializedAgent {
  name: string;
  description: string;
  executor: AgentExecutor;
}

class AgentOrchestrator {
  private agents: SpecializedAgent[] = [];
  private router: any;

  register(agent: SpecializedAgent) {
    this.agents.push(agent);
  }

  async route(input: string): Promise<string> {
    // Use LLM to pick the right agent
    const model = new ChatOpenAI({ model: "gpt-4o-mini", temperature: 0 });
    const agentList = this.agents
      .map((a) => `- ${a.name}: ${a.description}`)
      .join("\n");

    const routerPrompt = ChatPromptTemplate.fromTemplate(`
Given these specialized agents:
${agentList}

Which agent should handle this request? Reply with just the agent name.
Request: {input}`);

    const routerChain = routerPrompt.pipe(model).pipe(new StringOutputParser());
    const agentName = (await routerChain.invoke({ input })).trim();

    const agent = this.agents.find((a) => a.name === agentName);
    if (!agent) {
      return `No agent found for: ${input}`;
    }

    const result = await agent.executor.invoke({ input, chat_history: [] });
    return result.output;
  }
}

// Usage
const orchestrator = new AgentOrchestrator();
orchestrator.register({
  name: "code-reviewer",
  description: "Reviews code for bugs and best practices",
  executor: codeReviewAgent,
});
orchestrator.register({
  name: "data-analyst",
  description: "Analyzes data and generates reports",
  executor: dataAnalystAgent,
});
```

## Configuration-Driven Design

```typescript
// src/config/index.ts
import { z } from "zod";
import "dotenv/config";

const ConfigSchema = z.object({
  llm: z.object({
    provider: z.enum(["openai", "anthropic"]),
    model: z.string(),
    temperature: z.number().min(0).max(2).default(0),
    maxRetries: z.number().default(3),
  }),
  vectorStore: z.object({
    provider: z.enum(["pinecone", "faiss", "memory"]),
    indexName: z.string().optional(),
  }),
  server: z.object({
    port: z.number().default(8000),
    cors: z.boolean().default(true),
  }),
  langsmith: z.object({
    enabled: z.boolean().default(false),
    project: z.string().default("default"),
  }),
});

export type Config = z.infer<typeof ConfigSchema>;

export function loadConfig(): Config {
  return ConfigSchema.parse({
    llm: {
      provider: process.env.LLM_PROVIDER ?? "openai",
      model: process.env.LLM_MODEL ?? "gpt-4o-mini",
      temperature: Number(process.env.LLM_TEMPERATURE ?? 0),
    },
    vectorStore: {
      provider: process.env.VECTOR_STORE_PROVIDER ?? "memory",
      indexName: process.env.PINECONE_INDEX,
    },
    server: {
      port: Number(process.env.PORT ?? 8000),
    },
    langsmith: {
      enabled: process.env.LANGSMITH_TRACING === "true",
      project: process.env.LANGSMITH_PROJECT ?? "default",
    },
  });
}
```

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| Circular imports | Wrong layering | Core should never import from API layer |
| Provider not found | Unknown in factory | Add to factory switch statement |
| Chain not registered | Missing startup init | Register all chains in app bootstrap |
| Config validation fail | Missing env var | Add to `.env.example`, validate on startup |

## Resources

- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [LangChain Architecture Guide](https://js.langchain.com/docs/concepts/architecture/)
- [Domain-Driven Design](https://martinfowler.com/bliki/DomainDrivenDesign.html)

## Next Steps

Use `langchain-multi-env-setup` for environment management.
