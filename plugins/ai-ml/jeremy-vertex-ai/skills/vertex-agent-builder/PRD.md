# PRD: Vertex AI Agent Builder Skill

**Version:** 1.0.0
**Author:** Jeremy Longshore
**Date:** 2026-03-22
**Status:** Active
**Marketplace:** [tonsofskills.com](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io)
**Portfolio:** [jeremylongshore.com](https://jeremylongshore.com)

---

## Problem Statement

Deploying production AI agents on Vertex AI requires stitching together multiple GCP services -- Agent Engine for hosting, Vertex AI Search for RAG, Gemini models for generation, Cloud Functions or Cloud Run for tool backends, and IAM for security. Each service has its own API surface, quota model, and failure modes. Developers waste days on integration plumbing: embedding dimension mismatches break RAG indexes silently, function calling schemas drift from backend contracts, model region availability changes without warning, and cost overruns happen because there is no guardrail between a Gemini 2.5 Pro agent and a tight budget.

The Vertex AI Agent Builder skill eliminates this by producing a deployment-ready agent scaffold with RAG wiring, function calling contracts, evaluation prompts, cost controls, and monitoring -- all aligned with Vertex AI's actual API patterns.

## Target Users

| User | Context | Primary Need |
|------|---------|-------------|
| GCP developers | Building agents on Vertex AI | Scaffold that deploys to Agent Engine without manual fixes |
| ML engineers | Wiring RAG pipelines with Vertex AI Search | Correct chunking, embedding, and retrieval configuration |
| Platform teams | Standardizing agent deployments | Repeatable patterns with IAM, monitoring, and cost guardrails |
| Startups on GCP | Shipping an AI product fast | End-to-end from model selection to production endpoint |

## Success Criteria

1. **Deployment readiness**: Generated agent deploys to Agent Engine or Cloud Run with zero manual config edits
2. **RAG quality**: Retrieval pipeline returns cited, relevant passages with embedding dimensions matching the index
3. **Cost controls**: Every agent scaffold includes token budget configuration and model tier guidance
4. **Evaluation baseline**: At least 3 golden prompts and a smoke test that validates response structure
5. **API accuracy**: All generated code uses real Vertex AI SDK classes (`vertexai.generative_models`, `vertexai.preview.rag`, `google.cloud.aiplatform`)

## Functional Requirements

### FR-1: Scope Confirmation

Before generating anything, the skill confirms:
- Agent purpose (chat, extraction, routing, RAG)
- Deployment target (Agent Engine vs. Cloud Run vs. local-only)
- Model tier (gemini-2.0-flash for low latency, gemini-2.5-pro for complex reasoning)
- RAG requirements (document sources, citation needs, index strategy)
- Tool/function calling surface (external APIs, GCP services, databases)

### FR-2: Model and Region Selection

- Map use case to model: `gemini-2.0-flash` (general), `gemini-2.5-pro` (complex reasoning, large context)
- Validate region availability (not all models available in all regions)
- Default to `us-central1` (broadest model + quota availability)
- Include fallback region recommendation

### FR-3: RAG Pipeline Configuration

When retrieval is needed:
- Document ingestion plan (GCS source, chunking strategy, chunk size/overlap)
- Embedding model selection (`text-embedding-005` for English, `text-multilingual-embedding-002` for multi-language)
- Vertex AI Search corpus creation or Vertex AI RAG Engine index setup
- Citation-first response format (every claim backed by a source chunk)
- Index refresh strategy (manual vs. scheduled re-indexing)

### FR-4: Function Calling Setup

- Define tool schemas using Vertex AI's `FunctionDeclaration` format
- Map each function to a backend (Cloud Function, Cloud Run endpoint, or inline)
- Error contract: every tool returns structured success/failure responses
- Include schema validation tests

### FR-5: Evaluation Framework

- 3+ golden prompts covering happy path, edge cases, and refusal scenarios
- Offline evaluation script using `vertexai.evaluation` APIs
- Smoke test that validates deployed agent returns structured responses
- RAG-specific checks: citation presence, source relevance, hallucination detection

### FR-6: Deployment and Operations

- Deployment command/config for Agent Engine or Cloud Run
- Post-deploy health check (endpoint responds, model loaded, RAG index accessible)
- Cloud Monitoring alert recommendations (error rate, latency p95, token usage)
- Rollback procedure

## Non-Functional Requirements

### NFR-1: Latency

- Flash-tier agents: < 2s time-to-first-token for non-RAG queries
- RAG agents: < 5s end-to-end including retrieval
- Skill provides latency budget breakdown (retrieval vs. generation)

### NFR-2: Cost

- Default to `gemini-2.0-flash` unless complex reasoning is justified
- Include per-query cost estimate based on average token counts
- Token budget configuration in agent scaffold (max input/output tokens)

### NFR-3: Security

- No API keys or service account keys in generated files
- All secrets via environment variables or Secret Manager references
- IAM roles follow least-privilege: `roles/aiplatform.user` for inference, `roles/discoveryengine.editor` for RAG admin
- Workload Identity Federation recommended over exported keys

### NFR-4: Idempotency

- Running the skill twice with the same inputs produces the same scaffold
- Skill does not overwrite existing files unless explicitly confirmed

## Dependencies

| Dependency | Version | Purpose |
|-----------|---------|---------|
| `google-cloud-aiplatform` | >= 1.74.0 | Vertex AI SDK (models, evaluation, deployment) |
| `vertexai` | >= 1.74.0 | High-level Vertex AI API (GenerativeModel, RAG) |
| `google-cloud-discoveryengine` | >= 0.13.0 | Vertex AI Search / RAG corpus management |
| `google-cloud-storage` | >= 2.0 | Document ingestion from GCS |
| Python | >= 3.10 | Minimum runtime |
| GCP project | Billing enabled, Vertex AI API active | Required for all features |

## Out of Scope

- **LangChain/LlamaIndex integration**: This skill is Vertex AI-native. Use framework-specific skills for those.
- **Model fine-tuning**: Uses base Gemini models. Supervised tuning is a separate workflow.
- **Frontend/UI**: Agents are backend services. Chat UIs are a separate concern.
- **Multi-cloud**: Targets GCP exclusively (Vertex AI, Agent Engine, GCS, BigQuery).
- **Monitoring dashboard creation**: Provides alert recommendations but does not create Cloud Monitoring dashboards.
- **Data pipeline orchestration**: For Dataflow or Composer pipelines, use dedicated GCP skills.
