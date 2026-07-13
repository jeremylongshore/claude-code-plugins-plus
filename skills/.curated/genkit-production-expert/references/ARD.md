# ARD: Genkit Production Expert

> Part of [Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)

## System Context

The Genkit Production Expert operates within a developer's project to create, configure, and deploy Firebase Genkit flows. It interacts with the local codebase for implementation and Google Cloud services for model access and deployment.

```
Developer Request
       ↓
[Genkit Production Expert]
  ├── Reads: project config, existing flows, schemas
  ├── Writes: flows, tools, retrievers, deploy config
  └── Calls: genkit CLI, npm/pip, firebase deploy, gcloud
       ↓
Deployed Genkit Flow
  ├── Firebase Functions / Cloud Run
  ├── Gemini API (Vertex AI)
  ├── Vector Search (Firestore)
  └── OpenTelemetry Tracing
```

## Data Flow

1. **Input**: User request specifying the flow type (simple/multi-step/RAG/agent), target language (TypeScript/Python/Go), model preference, and deployment target (Firebase Functions/Cloud Run)
2. **Processing**: Scaffold project structure, define typed schemas, implement the flow with model bindings, add tool definitions or retrievers as needed, configure error handling and tracing, then deploy with auto-scaling parameters
3. **Output**: Complete flow implementation with schemas, deployment configuration (firebase.json or Cloud Run YAML), monitoring setup (OpenTelemetry traces, Firebase Console integration), and cost optimization report

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Schema-first design | Define Zod/Pydantic schemas before flow logic | Catches type errors at runtime boundaries, not deep inside flow execution |
| Gemini 2.5 Flash default | Flash for throughput, Pro for complex reasoning | 10x cheaper than Pro; sufficient for most flow types; upgrade only when quality demands |
| OpenTelemetry native | Built-in Genkit tracing over custom logging | Standard observability protocol; integrates with Cloud Monitoring without custom code |
| Firebase Functions for simple flows | Functions over Cloud Run for single-purpose flows | Zero infrastructure management, automatic scaling, sub-second deployment |
| Cloud Run for long flows | Cloud Run when execution exceeds 60s Functions limit | Configurable timeout up to 60 minutes; supports streaming responses |
| Error categorization | Distinct handling for SAFETY_BLOCK, QUOTA_EXCEEDED, schema errors | Each error type needs different recovery: retry, fallback, or user notification |
| Context caching for RAG | Cache embedding results for repeated document queries | Reduces token costs and latency for frequently accessed knowledge bases |

## Tool Usage Pattern

| Tool | Purpose |
|------|---------|
| Read | Inspect existing Genkit config, flow files, schema definitions, and package.json/requirements.txt |
| Write | Create new flow files, schema definitions, retriever implementations, and deployment configs |
| Edit | Patch existing flows to add tools, fix schemas, update model config, or add error handling |
| Grep | Search for import patterns, model usage, schema references, and configuration values |
| Glob | Discover project layout — flow files, test files, config files across the repository |
| Bash(cmd:*) | Run genkit CLI, npm/pip install, firebase deploy, test execution, and gcloud commands |

## Error Handling Strategy

| Error Class | Detection | Recovery |
|------------|-----------|----------|
| SAFETY_BLOCK | Gemini response contains `finishReason: SAFETY` | Log the blocked content category; retry with adjusted safety settings or sanitized input |
| QUOTA_EXCEEDED | 429 status or `RESOURCE_EXHAUSTED` error | Implement exponential backoff with jitter; queue requests; request quota increase |
| Schema validation failure | Zod/Pydantic throws validation error before `ai.generate()` | Return descriptive error message identifying the invalid field; do not call the model |
| Retriever empty results | Vector search returns zero documents above threshold | Lower similarity threshold; verify embeddings are indexed; check embedding model version |
| Deployment timeout | Firebase Functions cold start exceeds 60s | Increase memory allocation (512MB+); set min instances > 0; migrate to Cloud Run for long flows |

## Extension Points

- Custom model providers: add non-Google providers (OpenAI, Anthropic) via Genkit's plugin system
- Evaluation pipelines: integrate Genkit's `ai.evaluate()` for automated flow quality scoring
- Context caching: add prompt caching for repeated queries to reduce token costs
- Streaming responses: enable SSE streaming for chat-style flows on Cloud Run
- Multi-flow orchestration: chain multiple flows using Genkit's flow-to-flow calling pattern
- Custom retrievers: extend beyond Firestore vector search to Pinecone, Weaviate, or Elasticsearch
- Cost dashboards: generate Cloud Monitoring dashboards specific to token usage and model cost per flow
