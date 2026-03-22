# LangChain Skill Pack

> 24 production-grade skills for building LLM applications with LangChain.js and LangChain Python. Covers LCEL chains, agents with tool calling, RAG pipelines, vector stores, LangSmith tracing, and enterprise deployment patterns.

**Install:** `/plugin install langchain-pack@claude-code-plugins-plus`

**Links:** [Tons of Skills](https://tonsofskills.com/learn/langchain/) | [LangChain.js Docs](https://js.langchain.com/docs/) | [LangChain Python Docs](https://python.langchain.com/docs/) | [LangSmith](https://smith.langchain.com)

---

## What You Get

Real `@langchain/core` patterns -- not cookie-cutter templates. Every skill has working TypeScript and Python code using actual APIs: `ChatOpenAI`, `ChatAnthropic`, `ChatPromptTemplate.fromMessages()`, `RunnableSequence.from()`, `createToolCallingAgent`, `PineconeStore`, `OpenAIEmbeddings`, `FakeListChatModel` for testing, and `BaseCallbackHandler` for observability.

## Skills

### Getting Started (S01-S04)

| Skill | What It Teaches |
|-------|----------------|
| `langchain-install-auth` | Install `@langchain/core` + provider packages, configure API keys, verify connections |
| `langchain-hello-world` | First LCEL chain: `.pipe()` syntax, `ChatPromptTemplate`, `StringOutputParser`, Zod structured output, streaming |
| `langchain-local-dev-loop` | Project structure, Vitest setup, `FakeListChatModel` for unit tests, integration test gating |
| `langchain-sdk-patterns` | `withStructuredOutput`, `withFallbacks`, `.batch()`, `.stream()`, `RunnableLambda`, caching |

### Core Workflows (S05-S08)

| Skill | What It Teaches |
|-------|----------------|
| `langchain-core-workflow-a` | `RunnableSequence`, `RunnableParallel`, `RunnableBranch`, `RunnablePassthrough.assign()`, prompt composition |
| `langchain-core-workflow-b` | `tool()` with Zod schemas, `createToolCallingAgent`, `AgentExecutor`, `bindTools`, `RunnableWithMessageHistory` |
| `langchain-common-errors` | Exact error messages with fixes: import errors, auth failures, output parsing, agent loops, version conflicts |
| `langchain-debug-bundle` | `DebugTraceHandler` callback, environment snapshot, debug bundle generator, LangSmith trace export |

### Operations (S09-S12)

| Skill | What It Teaches |
|-------|----------------|
| `langchain-rate-limits` | `maxRetries`, `maxConcurrency`, `withFallbacks`, token bucket limiter, async semaphore batch |
| `langchain-security-basics` | Prompt injection defense, input sanitization, tool allowlisting, output validation, audit logging |
| `langchain-prod-checklist` | 30-item go-live checklist, startup validation script, health check endpoint, graceful shutdown |
| `langchain-upgrade-migration` | Import path migration, LLMChain-to-LCEL conversion, agent API migration, memory migration |

### Pro Skills (P13-P18)

| Skill | What It Teaches |
|-------|----------------|
| `langchain-ci-integration` | GitHub Actions workflow, `FakeListChatModel` unit tests, gated integration tests, RAG pipeline validation |
| `langchain-deploy-integration` | LangServe (Python), Express API (Node.js), Docker multi-stage, Cloud Run, health checks |
| `langchain-webhooks-events` | `BaseCallbackHandler`, webhook dispatch, SSE streaming endpoint, WebSocket integration, event aggregation |
| `langchain-performance-tuning` | Benchmarking, streaming, `.batch()` with concurrency, caching strategies, model routing, prompt optimization |
| `langchain-cost-tuning` | Token tracking callback, model tiering (gpt-4o-mini vs gpt-4o), caching, prompt compression, budget enforcement |
| `langchain-reference-architecture` | Layered architecture, LLM factory, chain registry, RAG architecture, multi-agent orchestration, Zod config |

### Flagship Skills (F19-F24)

| Skill | What It Teaches |
|-------|----------------|
| `langchain-multi-env-setup` | Dev/staging/prod configs with Zod validation, secret management (GCP/AWS), CI/CD environment isolation |
| `langchain-observability` | LangSmith zero-code tracing, custom metrics callback, Prometheus exporter, Grafana queries, alerting rules |
| `langchain-incident-runbook` | SEV1-4 classification, provider outage runbook, error rate diagnosis, latency spike mitigation, cost overrun response |
| `langchain-data-handling` | Document loaders, `RecursiveCharacterTextSplitter`, `OpenAIEmbeddings`, FAISS/Pinecone stores, full RAG chain |
| `langchain-enterprise-rbac` | Permission model, role-based model access, tenant-scoped vector stores, usage quotas, Express middleware |
| `langchain-migration-deep-dive` | Codebase scanner, OpenAI SDK to LangChain migration, RAG migration, side-by-side validation, feature-flagged rollout |

## Key APIs Covered

- **Models:** `ChatOpenAI`, `ChatAnthropic`, `OpenAIEmbeddings`
- **Prompts:** `ChatPromptTemplate.fromMessages()`, `ChatPromptTemplate.fromTemplate()`, `MessagesPlaceholder`
- **Runnables:** `RunnableSequence`, `RunnableParallel`, `RunnableBranch`, `RunnablePassthrough`, `RunnableLambda`
- **Output:** `StringOutputParser`, `StructuredOutputParser`, `.withStructuredOutput(zodSchema)`
- **Agents:** `createToolCallingAgent`, `AgentExecutor`, `tool()`, `bindTools()`
- **RAG:** `RecursiveCharacterTextSplitter`, `FaissStore`, `PineconeStore`, `.asRetriever()`
- **Memory:** `RunnableWithMessageHistory`, `ChatMessageHistory`
- **Callbacks:** `BaseCallbackHandler`, `FakeListChatModel`
- **Resilience:** `.withFallbacks()`, `maxRetries`, `maxConcurrency`

## License

MIT
