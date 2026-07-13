# ARD: Vertex AI Agent Builder

> Part of [Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)

## System Context

The Vertex AI Agent Builder skill generates agent scaffolds that target Google Cloud's Vertex AI platform. The agent interacts with multiple GCP services depending on the use case.

```
Developer (Claude Code)
    |
    v
Vertex AI Agent Builder Skill
    |
    +-- Reads: project context, user requirements, existing GCP config
    +-- Generates: agent code, RAG config, function schemas, eval prompts
    +-- Deploys to:
            |
            +-- Vertex AI Agent Engine (managed hosting)
            |       +-- Gemini Models (generation)
            |       +-- Vertex AI Search / RAG Engine (retrieval)
            |       +-- Cloud Functions (tool backends)
            |
            +-- Cloud Run (self-managed alternative)
            |
            +-- Supporting services:
                    +-- GCS (document storage)
                    +-- BigQuery (structured data, analytics)
                    +-- Firestore (session state, conversation history)
                    +-- Secret Manager (API keys, credentials)
                    +-- Cloud Monitoring (alerts, dashboards)
                    +-- IAM (service accounts, roles)
```

## Data Flow

1. **Input**: User describes the agent (purpose, data sources, tools, latency/cost constraints)
2. **Model selection**: Skill picks model tier and region based on requirements
3. **RAG wiring** (if needed): Configures document ingestion, embeddings, index, and retrieval
4. **Function calling**: Defines tool schemas and maps to backend implementations
5. **Scaffold generation**: Creates project structure with agent code, configs, tests, eval prompts
6. **Evaluation**: Runs golden prompts to validate agent behavior before deployment
7. **Deployment**: Generates deploy command, runs post-deploy health checks
8. **Monitoring**: Configures logging, alerting thresholds, and cost tracking

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Primary model | Gemini 2.0 Flash (default) | Best latency/cost ratio for most agent tasks; upgrade to 2.5 Pro only for complex reasoning |
| Hosting | Agent Engine over Cloud Run | Managed scaling, built-in session management, native Vertex AI integration |
| RAG backend | Vertex AI Search / RAG Engine | Native GCP service, handles chunking + embedding + retrieval in one API |
| Embeddings | `text-embedding-005` (768-dim) | Google's latest English embedding model, matches Vertex AI Search default |
| Citation strategy | Citation-first responses | Every claim must reference a source chunk; reduces hallucination, builds user trust |
| Function calling | Vertex AI native `FunctionDeclaration` | No external framework needed; schema validation built into the model API |
| Cost control | Token budgets + model tiering | `max_output_tokens` caps runaway generation; flash-first policy cuts cost 10-20x vs pro |

## Tool Usage Pattern

| Tool | Purpose |
|------|---------|
| `Read` | Examine existing project files, GCP config, service account setup |
| `Write` | Create scaffold files (agent code, RAG config, function schemas, tests) |
| `Edit` | Modify existing files (add tools, update model config, adjust prompts) |
| `Grep` | Find existing patterns, check for credential leaks, locate config files |
| `Bash(cmd:*)` | Run `gcloud` commands, deploy agents, execute tests, check quotas |

## Error Handling Strategy

| Error Class | Detection | Recovery |
|------------|-----------|----------|
| Model not available in region | `404` or `INVALID_ARGUMENT` on `GenerativeModel` init | Switch to `us-central1` or fall back to available model |
| Vertex AI API not enabled | `403 PERMISSION_DENIED: Vertex AI API has not been used` | Run `gcloud services enable aiplatform.googleapis.com` |
| RAG index dimension mismatch | Retrieval returns empty results despite matching docs | Verify embedding model dimensions match index config (768 for `text-embedding-005`) |
| Function calling schema error | Model returns `INVALID_ARGUMENT` on tool call | Validate `FunctionDeclaration` schema: check types, required fields, enum values |
| Quota exceeded | `429 RESOURCE_EXHAUSTED` on model or Agent Engine API | Suggest region change, request quota increase, or switch to flash tier |
| IAM permission denied | `403` on any GCP API call | Identify missing role, provide exact `gcloud projects add-iam-policy-binding` command |
| Agent Engine deploy failure | Build or health check fails during deployment | Check container logs, verify dependencies, validate agent entrypoint |
| Cost overrun | Token usage exceeds budget threshold | Enforce `max_output_tokens`, switch to flash model, add usage alerts |

## Extension Points

- **Custom tools**: Add `FunctionDeclaration` schemas and connect to Cloud Function / Cloud Run backends
- **Multi-agent orchestration**: Compose agents using Agent Engine's sub-agent routing
- **Alternative RAG sources**: Swap Vertex AI Search for BigQuery vector search or AlloyDB pgvector
- **Evaluation expansion**: Add automated evaluation datasets, A/B prompt testing, latency benchmarks
- **Alternative deployment**: Cloud Run for custom container control, GKE for high-scale workloads
- **Grounding**: Enable Google Search grounding for real-time web information alongside RAG
