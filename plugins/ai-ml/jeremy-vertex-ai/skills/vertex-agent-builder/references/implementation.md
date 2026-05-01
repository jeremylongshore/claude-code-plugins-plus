# Vertex AI Agent Builder -- Implementation Guide

## How the Skill Works

1. **Scope confirmation**: Determines agent purpose, deployment target, model tier, and RAG needs
2. **Model + region selection**: Maps use case to model and validates regional availability
3. **RAG pipeline design** (if needed): Configures document ingestion, embeddings, index, and retrieval
4. **Function calling setup**: Defines tool schemas and backend wiring
5. **Scaffold generation**: Creates project structure with all required files
6. **Evaluation**: Runs golden prompts to validate agent behavior
7. **Deployment**: Generates deploy commands and post-deploy health checks

## Project Structure

```
agent-project/
├── agent.py                    # Main agent with model, tools, and system instruction
├── rag_config.py               # RAG corpus setup, embedding config, ingestion (if RAG)
├── tools/
│   ├── __init__.py
│   └── custom_functions.py     # FunctionDeclaration schemas + backend handlers
├── eval/
│   ├── golden_prompts.json     # Test prompts with expected behaviors
│   └── run_eval.py             # Offline evaluation script
├── deploy.sh                   # Deployment commands for Agent Engine or Cloud Run
├── requirements.txt            # Pinned dependencies
├── .env.example                # Required environment variables (no values)
└── README.md                   # Setup and usage instructions
```

## Model and Region Selection Logic

**Model selection**:

| Requirement | Model | Reason |
|------------|-------|--------|
| General chat, Q&A, summarization | `gemini-2.0-flash` | Lowest latency, lowest cost, sufficient quality |
| Complex reasoning, multi-step analysis | `gemini-2.5-pro` | Best quality, supports thinking/reasoning traces |
| Multimodal extraction (PDF, images) | `gemini-2.5-pro` | Superior vision capabilities for structured extraction |
| High-volume, cost-sensitive | `gemini-2.0-flash` | 10-20x cheaper than pro tier |

**Region selection**:

| Priority | Region | Notes |
|----------|--------|-------|
| Default | `us-central1` | Broadest model availability, highest quotas, Agent Engine GA |
| EU data residency | `europe-west1` | GDPR compliance, Agent Engine available |
| Asia-Pacific | `asia-southeast1` | Best latency for APAC users |
| Fallback | Check `gcloud ai models list --region=REGION` | Not all models available everywhere |

## RAG Pipeline Design

### Pipeline stages

```
Documents (GCS/BigQuery)
    |
    v
Chunking (512 tokens, 100 overlap)
    |
    v
Embeddings (text-embedding-005, 768 dims)
    |
    v
Vertex AI RAG Engine Index
    |
    v
Retrieval (similarity_top_k=5)
    |
    v
Generation (Gemini + retrieved context)
    |
    v
Response with citations
```

### Chunking strategy

- **Default**: 512 tokens per chunk, 100 token overlap
- **Long documents** (legal, technical): 1024 tokens, 200 overlap for more context
- **Short documents** (FAQs, KB articles): 256 tokens, 50 overlap for precision
- Overlap prevents splitting critical information across chunk boundaries

### Embedding model selection

| Model | Dimensions | Use Case |
|-------|-----------|----------|
| `text-embedding-005` | 768 | English-only documents (recommended default) |
| `text-multilingual-embedding-002` | 768 | Multi-language document collections |

**Critical**: Embedding dimensions must match between ingestion and query time. Mismatched dimensions cause silent retrieval failures (empty results, no error).

### Index refresh

- **Manual**: Call `rag.import_files()` after document updates
- **Scheduled**: Cloud Scheduler triggers a Cloud Function that re-imports
- **Incremental**: Import only new/changed files using GCS event notifications

## Function Calling Setup

Every function uses `FunctionDeclaration` with name, description, and JSON Schema parameters. See `references/examples.md` Example 3 for a full implementation.

**Best practices**:
- Descriptions must be specific enough for the model to choose the right tool
- Use `enum` constraints to prevent invalid parameter values
- Mark `required` fields explicitly; optional fields get sensible defaults
- Return structured JSON from backends so the model can reason about results

## Evaluation Framework

### Golden prompts (`eval/golden_prompts.json`)

Each entry has: `prompt`, `expected_behavior`, and `checks` (array of assertions). Cover three categories:
- **Happy path**: Expected domain question with citation check
- **Out of scope**: Off-topic question that should be declined
- **Safety**: Dangerous request that must be refused with no tool calls

### Offline evaluation (`eval/run_eval.py`)

Uses `vertexai.evaluation` for automated quality checks:

```python
from vertexai.evaluation import EvalTask, MetricPromptTemplate

eval_task = EvalTask(
    dataset=eval_dataset,
    metrics=["fluency", "groundedness", "fulfillment"],
    experiment="agent-v1-eval",
)
result = eval_task.evaluate(model=model)
```

### Smoke tests (post-deploy)

```bash
# Verify agent endpoint responds
curl -s -o /dev/null -w "%{http_code}" \
  -X POST "https://us-central1-aiplatform.googleapis.com/v1/projects/PROJECT/locations/us-central1/publishers/google/models/gemini-2.0-flash:generateContent" \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"Hello"}]}]}'
# Expected: 200
```

## Deployment Pipeline

```
Local Development        Staging                    Production
-------------------      ----------------------     -------------------------
vertexai.init()          Deploy to Agent Engine      Deploy with monitoring
python agent.py          (staging project)           (prod project)
pytest eval/             Automated eval suite        Budget alerts active
Manual golden prompts    Latency benchmarks          Cloud Monitoring alerts
                         IAM audit                   Rollback procedure ready
```

**Deploy to Agent Engine**:
```bash
# Using the Vertex AI SDK (ReasoningEngine)
python -c "
from vertexai.preview import reasoning_engines
agent = reasoning_engines.ReasoningEngine.create(
    reasoning_engine=MyAgent(),
    display_name='support-agent-v1',
    requirements=['google-cloud-aiplatform>=1.74.0'],
)
print(f'Deployed: {agent.resource_name}')
"
```

**Health check**:
```bash
# List deployed agents
gcloud ai reasoning-engines list --region=us-central1

# Query deployed agent
gcloud ai reasoning-engines query RESOURCE_ID --region=us-central1 --request='{"input": {"prompt": "test"}}'
```

## Monitoring and Alerting

**Key metrics to track**:

| Metric | Threshold | Alert |
|--------|-----------|-------|
| Error rate (5xx) | > 1% over 5 min | PagerDuty / Slack |
| Latency p95 | > 5s (flash) / > 15s (pro) | Email warning |
| Token usage daily | > budget / 30 | Billing alert |
| RAG retrieval empty rate | > 20% | Index staleness check |

**Logging**:
```bash
# View agent inference logs
gcloud logging read 'resource.type="aiplatform.googleapis.com/PublisherModel"' \
  --project=PROJECT_ID --limit=50 --format=json

# Filter for errors only
gcloud logging read 'resource.type="aiplatform.googleapis.com/PublisherModel" AND severity>=ERROR' \
  --project=PROJECT_ID --limit=20
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
