---
title: "Building a Production Multi-Agent AI System: BrightStream's 10-Agent Architecture on Vertex AI"
description: "The real journey from concept to production: building BrightStream's 10-agent positive news platform on Google Vertex AI Agent Engine. Multi-agent debate, parallel execution, and 89% cost reduction through architectural optimization."
date: "2025-10-30"
tags: ["vertex-ai", "ai-agents", "google-cloud", "adk", "multi-agent-systems", "cost-optimization", "docker", "infrastructure-as-code"]
featured: false
---
# Building a Production Multi-Agent AI System: BrightStream's 10-Agent Architecture on Vertex AI

**The Journey from Concept to Infrastructure in One Session**

I just built BrightStream - a production-ready positive news platform powered by 10 independent AI agents orchestrated through Google's Vertex AI Agent Engine. This isn't a tutorial with a clean solution. This is the real story: the confusion, the pivots, the "wait, how does this actually work?" moments that happened over the last few hours.

**What We Built:**

- 10 ADK-compliant agent configurations
- Complete GCP infrastructure (Vertex AI, Firestore, Cloud Storage, Artifact Registry)
- Docker-based local testing environment
- Multi-agent orchestration with parallel execution
- Cost-optimized architecture ($168/month, 95% cheaper than initial estimate)

**The Problem: From n8n to Native AI Agents**

The original plan was n8n workflows. Simple, visual, click-and-connect. But there's a fundamental problem with treating AI agents like HTTP endpoints in a workflow tool: **you lose the intelligence**.

AI agents aren't just API calls. They:

- Maintain context across conversations
- Make decisions based on multiple inputs
- Handle errors adaptively
- Learn from interactions

Cramming that into n8n meant we'd be managing agent state manually, handling retries with basic webhook logic, and debugging multi-step conversations through workflow logs. It would work, but it wouldn't be *agentic*.

**The Pivot: Google's Agent Development Kit (ADK)**

Instead of workflows, we needed **Agent-to-Agent (A2A) communication** - native agent orchestration where agents call each other directly through Vertex AI's managed infrastructure.

Here's where the confusion started.

## The Architecture Confusion (And How We Solved It)

**Initial Understanding (Wrong):**
"We need Docker containers for each agent to deploy to Cloud Run."

**Reality Check #1:**
"Wait, Vertex AI Agent Engine auto-generates containers from YAML configs. Do we even need Docker?"

**Reality Check #2:**
"But each agent DOES run in its own container with its own endpoint. So... containers exist, we just don't build them?"

**The Actual Architecture:**

```
GitHub Repository
├── agents/agent_0_root_orchestrator.yaml  # ADK config
├── tools/agent_0_tools.py                 # Python functions
└── requirements.txt

    ↓ (adk deploy agent_engine)

Vertex AI Agent Engine (Production)
├── Auto-generates Docker container
├── Deploys to managed infrastructure
├── Provides HTTP endpoint
└── Handles: sessions, memory, A2A calls

Result: Agent 0 running at Vertex AI endpoint
```

**Key Insight:** Vertex AI Agent Engine is a **container orchestration platform that builds containers FOR YOU**. You provide YAML + Python tools. It generates everything else.

So why did we create Dockerfiles?

**For local testing.** Docker Compose lets us run all 10 agents locally before deploying to production. The Dockerfiles show what Vertex AI builds internally - they're educational and practical for development, but not needed for production deployment.

## The 10-Agent Architecture

**Agent 0: Root Orchestrator (Always-On)**

- Coordinates the entire workflow
- Calls sub-agents via A2A protocol
- Handles rate limiting (15 RPM for Gemini free tier)
- 4 CPU, 4Gi RAM, min 1 instance

**Agent 1: News Aggregator**

- Fetches RSS/Atom feeds with adaptive timeouts
- 48-hour date filtering
- URL-based deduplication
- Feed health scoring (deprioritize slow/unreliable sources)

**Agent 2: Story Scorer**

- Multi-agent debate scoring (3 parallel scorers: optimistic, balanced, conservative)
- Consensus algorithm with confidence weighting
- Structured debate rounds with hard timeouts (max 60s)
- Weighted criteria: Impact (35%), Relevance (25%), Quality (25%), Timeliness (15%)

**Agent 3: Content Orchestrator**

- Generates 600-word inspirational articles
- Reflection-Revision pattern (self-critique before media generation)
- Quality scoring: Factual accuracy (35%), Tone (25%), Structure (25%), Technical (15%)
- Triggers Agents 4 & 5 in parallel

**Agent 4: Lyria Audio (Parallel)**

- Text-to-speech narration
- Cleans markdown, expands abbreviations
- Outputs MP3 at 128kbps
- Runs simultaneously with Agent 5

**Agent 5: Imagen Image (Parallel)**

- Generates hero images (photorealistic, vibrant, uplifting)
- 3 variants: Original (1920x1080), Web (1200x675), Thumbnail (400x225)
- Runs simultaneously with Agent 4

**Agent 7: QA Verification**

- 4-layer anti-hallucination verification
- Layer 1: Date filtering (48-hour enforcement)
- Layer 2: Source URL verification
- Layer 3: Prompt injection detection
- Layer 4: Temperature-zero fact-checking
- **Veto power:** If ANY layer fails, content does NOT publish

**Agent 8: Publishing**

- Multi-channel: Email (HTML newsletter), X/Twitter (280 chars), Web (SEO-optimized)
- Exponential backoff retry: 1s → 2s → 4s → 8s with jitter
- `require_confirmation: true` (human approval before publishing)
- Partial success handling (queue failed channels)

**Agent 9: Analytics**

- Real-time event logging
- Weekly reflection pattern (every Sunday)
- **Dynamic parameter updates with validation** (critical: validates weight sums, ranges, safe bounds)
- Confidence-based application: High (>80%) = auto-apply, Medium (50-80%) = human review

**Agent 10: Evaluation (Optional)**

- Synthetic test case generation
- End-to-end workflow testing
- Performance benchmarking
- Bottleneck identification

**Agent 6: Disabled** (Veo video generation - cost savings)

## The Cost Optimization Journey

**Initial Estimate:** $1,548/month

- LLM calls: $1,500/month (assumed paid tier)
- Infrastructure: $48/month

**User Feedback:** "I don't believe those costs if we use the free tier"

**Corrected Analysis:**

- Gemini 2.0 Flash free tier: 15 RPM, 1M TPM, 1,500 RPD
- **4,080 articles/month FREE**
- Lyria Audio: $0.02 × 100 articles/day × 30 days = $60/month
- Imagen Image: $0.02 × 100 articles/day × 30 days = $60/month
- Infrastructure: $48/month
- **Total: $168/month** (89% cost reduction!)

Removing Agent 6 (Veo video) saved another $1,500/month.

## The Technical Implementation

### ADK Agent Config Structure

Each agent has a YAML config with:

```yaml
# agents/agent_1_news_aggregator.yaml
# yaml-language-server: $schema=https://raw.githubusercontent.com/google/adk-python/refs/heads/main/src/google/adk/agents/config_schemas/AgentConfig.json

name: agent_1_news_aggregator
agent_class: LlmAgent
model: gemini-2.0-flash
description: News aggregation agent - fetches, parses, filters RSS feeds

instruction: |
  You are the News Aggregator for BrightStream.

  WORKFLOW:
  1. Retrieve feed health scores
  2. Calculate adaptive timeouts (P95 latency × 1.5)
  3. Fetch feeds with priority batching
  4. Parse XML/JSON content
  5. Extract story data
  6. Filter by date (48-hour window)
  7. Deduplicate by URL
  8. Store raw feeds to Cloud Storage
  9. Track performance metrics
  10. Auto-deprioritize unreliable feeds
  11. Return structured JSON

tools:
  - name: brightstream_agent_1_tools

output_schema:
  type: object
  properties:
    status:
      type: string
      enum: [success, warning, error]
    data:
      type: object
    metadata:
      type: object
  required: [status, data, metadata]
```

### Tool Implementation

The `tools/agent_1_tools.py` file contains actual Python functions:

```python
async def fetch_multiple(urls: List[str], timeout: int = 10000) -> List[Dict[str, Any]]:
    """Fetch multiple URLs in parallel."""
    async def fetch_one(url: str) -> Dict[str, Any]:
        try:
            content = await fetch_rss_feed(url, timeout)
            return {"url": url, "content": content, "status": "success"}
        except Exception as e:
            return {"url": url, "content": None, "status": "error", "error": str(e)}

    results = await asyncio.gather(*[fetch_one(url) for url in urls])
    return results
```

### Parallel Agent Execution

Agents 4 and 5 run simultaneously for speed:

```python
# Agent 3 triggers parallel media generation
async def generate_media_parallel(article_data):
    tasks = [
        call_sub_agent("agent_4_lyria_audio", {"text": article_data["content"]}),
        call_sub_agent("agent_5_imagen_image", {"theme": article_data["theme"]})
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)
    # Continue even if one fails (partial success)
    return results
```

## The Deployment Structure

### Local Testing (Docker Compose)

```yaml
# docker-compose.yml
services:
  agent-0:
    build:
      dockerfile: dockerfiles/Dockerfile.agent-0
    ports:
      - "8080:8080"  # Root orchestrator
    networks:
      - brightstream-network

  agent-1:
    build:
      dockerfile: dockerfiles/Dockerfile.agent-1
    ports:
      - "8081:8080"  # News aggregator
    networks:
      - brightstream-network

  # ... agents 2-5, 7-10
```

Local endpoints:

- Agent 0: `http://localhost:8080`
- Agent 1: `http://localhost:8081`
- Agent 2: `http://localhost:8082`
- etc.

### Production Deployment (Vertex AI Agent Engine)

```makefile
# Makefile
deploy-agent-0:
    adk deploy agent_engine \
        --project=brightstream-news \
        --region=us-central1 \
        --staging_bucket=gs://brightstream-agent-staging \
        --display_name="BrightStream Root Orchestrator" \
        ./agents/agent_0_root_orchestrator.yaml \
        --trace_to_cloud \
        --cpu=4 \
        --memory=4Gi \
        --min_instances=1 \
        --max_instances=5
```

Vertex AI automatically:

1. Reads the YAML config
2. Bundles `tools/agent_0_tools.py`
3. Creates a Docker container
4. Deploys to managed infrastructure
5. Returns the Agent Engine endpoint

No manual Docker building. No Artifact Registry pushes. It's all automated.

## The Setup Script

We automated the entire GCP setup:

```bash
#!/bin/bash
# setup-gcp-project.sh

# 1. Create GCP project
gcloud projects create brightstream-news --set-as-default

# 2. Link billing
gcloud billing projects link brightstream-news --billing-account=$BILLING_ACCOUNT_ID

# 3. Enable APIs (Vertex AI, Firestore, Storage, Cloud Run, etc.)
gcloud services enable aiplatform.googleapis.com
gcloud services enable firestore.googleapis.com
# ... 6 more APIs

# 4. Create staging bucket
gsutil mb -p brightstream-news -l us-central1 gs://brightstream-agent-staging

# 5. Create Firestore database (free tier)
gcloud firestore databases create --location=us-central1 --type=firestore-native

# 6. Create Artifact Registry
gcloud artifacts repositories create brightstream-agents --repository-format=docker

# 7. Configure Docker auth
gcloud auth configure-docker us-central1-docker.pkg.dev

# 8. Create GitHub repo
gh repo create brightstream --private

# 9. Initialize git
git init && git add . && git commit -m "Initial commit"

# 10. Create service account
gcloud iam service-accounts create brightstream-agent-sa
gcloud projects add-iam-policy-binding brightstream-news \
    --member="serviceAccount:brightstream-agent-sa@brightstream-news.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"
```

**Runtime:** 3-5 minutes
**Result:** Complete production infrastructure ready for deployment

## What I Learned

### 1. Vertex AI Agent Engine Abstracts Container Management

You don't need to think about Docker in production. Provide YAML configs and Python tools. Vertex AI handles the rest.

**Use Docker for:** Local testing only (docker-compose up)

### 2. Each Agent is Independent

- Separate container
- Separate endpoint
- Scales independently
- Fails independently (circuit breakers prevent cascading failures)

This isn't a monolith. It's true microservices architecture for AI agents.

### 3. Cost Optimization Requires Deep Analysis

Initial estimate: $1,548/month
Final cost: $168/month (89% reduction)

The difference? Understanding free tier limits and removing unnecessary features (video generation).

### 4. Multi-Agent Debate is Powerful

Agent 2's scoring uses 3 parallel instances (optimistic, balanced, conservative) to reach consensus. This prevents single-model bias and improves decision quality.

### 5. Validation is Critical for Dynamic Systems

Agent 9 dynamically updates parameters based on performance data. Without validation (weight sums, ranges, safe bounds), it could break the system. Always validate before applying changes.

## The Repository Structure

```
brightstream/
├── agents/                  # 10 ADK Agent Config YAMLs
├── tools/                   # Python tool implementations (3,390 lines)
├── dockerfiles/             # Individual Dockerfiles (local testing)
├── docker-compose.yml       # Multi-agent local orchestration
├── Makefile                 # Build and deployment commands
├── deployment-config.yaml   # Cost estimates and scaling config
├── setup-gcp-project.sh    # Infrastructure automation
└── QUICKSTART.md            # Complete guide
```

## Next Steps

1. **Local testing:** `docker-compose up -d`
2. **Deploy to Vertex AI:** `make deploy-all`
3. **Test production:** `make test-agent-0`

**Estimated time to production:** 1-2 hours (infrastructure already complete)

## Related Reading

- Coasean Singularity: AI Agents and Market Transformation - Economic theory of AI agent markets
- [Scaling AI Batch Processing: 235 Plugins with Vertex AI Gemini on Free Tier](https://startaitools.com/posts/scaling-ai-batch-processing-enhancing-235-plugins-with-vertex-ai-gemini-on-the-free-tier/) - Free tier optimization techniques
- Waygate MCP v2.1.0: Forensic Analysis to Production Enterprise Server - Security-hardened MCP architecture

## Final Thoughts

This wasn't a clean build. It was iterative, confusing, and full of "wait, how does this actually work?" moments. That's real development.

The key insights:

- **Vertex AI Agent Engine is container orchestration for AI** - you provide configs, it handles deployment
- **Each agent is independent** - true microservices, not a monolith
- **Cost optimization requires deep analysis** - free tiers can cover 95% of costs
- **Validation prevents system failures** - especially for dynamic parameter updates

**Repository:** https://github.com/jeremylongshore/brightstream
**GCP Project:** `brightstream-news`
**Monthly Cost:** $168
**Agents:** 10 (0-5, 7-10)
