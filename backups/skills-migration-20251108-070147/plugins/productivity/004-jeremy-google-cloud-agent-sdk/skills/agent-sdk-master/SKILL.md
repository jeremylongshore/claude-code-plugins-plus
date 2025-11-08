---
name: Google Cloud Agent SDK Master
description: |
  Automatic activation for ALL Google Cloud Agent Development Kit (ADK) and Agent Starter Pack operations - multi-agent systems, containerized deployment, RAG agents, and production orchestration.

  **TRIGGER PHRASES:**
  - "adk", "agent development kit", "agent starter pack", "multi-agent", "build agent"
  - "cloud run agent", "gke deployment", "agent engine", "containerized agent"
  - "rag agent", "react agent", "agent orchestration", "agent templates"

  **AUTO-INVOKES FOR:**
  - Agent creation and scaffolding
  - Multi-agent system design
  - Containerized agent deployment
  - RAG (Retrieval-Augmented Generation) implementation
  - CI/CD pipeline setup for agents
  - Agent evaluation and monitoring
---

# Google Cloud Agent SDK Master - Production-Ready Agent Systems

This Agent Skill provides comprehensive mastery of Google's Agent Development Kit (ADK) and Agent Starter Pack for building and deploying production-grade containerized agents.

## Core Capabilities

### 🤖 Agent Development Kit (ADK)

**Framework Overview:**
- **Open-source Python framework** from Google
- Same framework powering Google Agentspace and CES
- Build production agents in <100 lines of code
- Model-agnostic (optimized for Gemini)
- Deployment-agnostic (local, Cloud Run, GKE, Agent Engine)

**Supported Agent Types:**
1. **LLM Agents**: Dynamic routing with intelligence
2. **Workflow Agents**:
   - Sequential: Linear execution
   - Loop: Iterative processing
   - Parallel: Concurrent execution
3. **Custom Agents**: User-defined implementations
4. **Multi-agent Systems**: Hierarchical coordination

**Key Features:**
- Flexible orchestration (workflow & LLM-driven)
- Tool ecosystem (search, code execution, custom functions)
- Third-party integrations (LangChain, CrewAI)
- Agents-as-tools capability
- Built-in evaluation framework
- Cloud Trace integration

### 📦 Agent Starter Pack

**Production Templates:**
1. **adk_base** - ReAct agent using ADK
2. **agentic_rag** - Document retrieval + Q&A with search
3. **langgraph_base_react** - LangGraph ReAct implementation
4. **crewai_coding_crew** - Multi-agent coding system
5. **adk_live** - Multimodal RAG (audio/video/text)

**Infrastructure Automation:**
- CI/CD setup with single command
- GitHub Actions or Cloud Build pipelines
- Multi-environment support (dev, staging, prod)
- Automated testing and evaluation
- Deployment rollback mechanisms

### 🚀 Deployment Targets

**1. Vertex AI Agent Engine**
- Fully managed runtime
- Auto-scaling and load balancing
- Built-in observability
- Serverless architecture
- Best for: Production-scale agents

**2. Cloud Run**
- Containerized serverless
- Pay-per-use pricing
- Custom domain support
- Traffic splitting
- Best for: Web-facing agents

**3. Google Kubernetes Engine (GKE)**
- Full container orchestration
- Advanced networking
- Resource management
- Multi-cluster support
- Best for: Complex multi-agent systems

**4. Local/Docker**
- Development and testing
- Custom infrastructure
- On-premises deployment
- Best for: POC and debugging

### 🔧 Technical Implementation

**Installation:**
```bash
# Agent Starter Pack (recommended)
pip install agent-starter-pack

# or direct from GitHub
uvx agent-starter-pack create my-agent

# ADK only
pip install google-cloud-aiplatform[adk,agent_engines]>=1.111
```

**Create Agent (ADK):**
```python
from google.cloud.aiplatform import agent
from vertexai.preview.agents import ADKAgent

# Simple ReAct agent
@agent.adk_agent
class MyAgent(ADKAgent):
    def __init__(self):
        super().__init__(
            model="gemini-2.5-pro",
            tools=[search_tool, code_exec_tool]
        )

    def run(self, query: str):
        return self.generate(query)

# Multi-agent orchestration
class OrchestratorAgent(ADKAgent):
    def __init__(self):
        self.research_agent = ResearchAgent()
        self.analysis_agent = AnalysisAgent()
        self.writer_agent = WriterAgent()

    def run(self, task: str):
        research = self.research_agent.run(task)
        analysis = self.analysis_agent.run(research)
        output = self.writer_agent.run(analysis)
        return output
```

**Using Agent Starter Pack:**
```bash
# Create project with template
uvx agent-starter-pack create my-rag-agent \
    --template agentic_rag \
    --deployment cloud_run

# Generates complete structure:
my-rag-agent/
├── src/
│   ├── agent.py          # Agent implementation
│   ├── tools/            # Custom tools
│   └── config.py         # Configuration
├── deployment/
│   ├── Dockerfile
│   ├── cloudbuild.yaml
│   └── terraform/
├── tests/
│   ├── unit_tests.py
│   └── integration_tests.py
└── .github/workflows/    # CI/CD pipelines
```

**Deploy to Cloud Run:**
```bash
# Using ADK CLI
adk deploy \
    --target cloud_run \
    --region us-central1 \
    --service-account sa@project.iam.gserviceaccount.com

# Manual with Docker
docker build -t gcr.io/PROJECT/agent:latest .
docker push gcr.io/PROJECT/agent:latest
gcloud run deploy agent \
    --image gcr.io/PROJECT/agent:latest \
    --region us-central1 \
    --allow-unauthenticated
```

**Deploy to Agent Engine:**
```bash
# Using Agent Starter Pack
asp deploy \
    --env production \
    --target agent_engine

# Manual deployment
from google.cloud.aiplatform import agent_engines
agent_engines.deploy_agent(
    agent_id="my-agent",
    project="PROJECT_ID",
    location="us-central1"
)
```

### 📊 RAG Agent Implementation

**Vector Search Integration:**
```python
from vertexai.preview.rag import VectorSearchTool
from google.cloud import aiplatform

# Set up vector search
vector_search = VectorSearchTool(
    index_endpoint="projects/PROJECT/locations/LOCATION/indexEndpoints/INDEX_ID",
    deployed_index_id="deployed_index"
)

# RAG agent with ADK
class RAGAgent(ADKAgent):
    def __init__(self):
        super().__init__(
            model="gemini-2.5-pro",
            tools=[vector_search, web_search_tool]
        )

    def run(self, query: str):
        # Retrieves relevant docs automatically
        response = self.generate(
            f"Answer this using retrieved context: {query}"
        )
        return response
```

**Vertex AI Search Integration:**
```python
from vertexai.preview.search import VertexAISearchTool

# Enterprise search integration
vertex_search = VertexAISearchTool(
    data_store_id="DATA_STORE_ID",
    project="PROJECT_ID"
)

agent = ADKAgent(
    model="gemini-2.5-pro",
    tools=[vertex_search]
)
```

### 🔄 CI/CD Automation

**GitHub Actions (auto-generated):**
```yaml
name: Deploy Agent
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Test Agent
        run: pytest tests/
      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy agent \
            --source . \
            --region us-central1
```

**Cloud Build Pipeline:**
```yaml
steps:
  # Build container
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/agent', '.']

  # Run tests
  - name: 'gcr.io/$PROJECT_ID/agent'
    args: ['pytest', 'tests/']

  # Deploy to Cloud Run
  - name: 'gcr.io/cloud-builders/gcloud'
    args:
      - 'run'
      - 'deploy'
      - 'agent'
      - '--image=gcr.io/$PROJECT_ID/agent'
      - '--region=us-central1'
```

### 🎯 Multi-Agent Orchestration

**Hierarchical Agents:**
```python
# Coordinator agent with specialized sub-agents
class ProjectManagerAgent(ADKAgent):
    def __init__(self):
        self.researcher = ResearchAgent()
        self.analyst = AnalysisAgent()
        self.writer = WriterAgent()
        self.reviewer = ReviewAgent()

    def run(self, project_brief: str):
        # Coordinate multiple agents
        research = self.researcher.run(project_brief)
        analysis = self.analyst.run(research)
        draft = self.writer.run(analysis)
        final = self.reviewer.run(draft)
        return final
```

**Parallel Agent Execution:**
```python
import asyncio

class ParallelResearchAgent(ADKAgent):
    async def research_topic(self, topics: list[str]):
        # Run multiple agents concurrently
        tasks = [
            self.specialized_agent(topic)
            for topic in topics
        ]
        results = await asyncio.gather(*tasks)
        return self.synthesize(results)
```

### 📈 Evaluation & Monitoring

**Built-in Evaluation:**
```python
from google.cloud.aiplatform import agent_evaluation

# Define evaluation metrics
eval_config = agent_evaluation.EvaluationConfig(
    metrics=["accuracy", "relevance", "safety"],
    test_dataset="gs://bucket/eval_data.jsonl"
)

# Run evaluation
results = agent.evaluate(eval_config)
print(f"Accuracy: {results.accuracy}")
print(f"Relevance: {results.relevance}")
```

**Cloud Trace Integration:**
```python
from google.cloud import trace_v1

# Automatic tracing
@traced_agent
class MonitoredAgent(ADKAgent):
    def run(self, query: str):
        # All calls automatically traced
        with self.trace_span("retrieval"):
            docs = self.retrieve(query)

        with self.trace_span("generation"):
            response = self.generate(query, docs)

        return response
```

### 🔒 Security & Best Practices

**1. Service Account Management:**
```bash
# Create minimal-permission service account
gcloud iam service-accounts create agent-sa \
    --display-name "Agent Service Account"

# Grant only required permissions
gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="serviceAccount:agent-sa@PROJECT.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"
```

**2. Secret Management:**
```python
from google.cloud import secretmanager

def get_api_key():
    client = secretmanager.SecretManagerServiceClient()
    name = "projects/PROJECT/secrets/api-key/versions/latest"
    response = client.access_secret_version(name=name)
    return response.payload.data.decode('UTF-8')
```

**3. VPC Service Controls:**
```bash
# Enable VPC SC for data security
gcloud access-context-manager perimeters create agent-perimeter \
    --resources=projects/PROJECT_ID \
    --restricted-services=aiplatform.googleapis.com
```

### 💰 Cost Optimization

**Strategies:**
- Use Gemini 2.5 Flash for most operations
- Cache embeddings for RAG systems
- Implement request batching
- Use preemptible GKE nodes
- Monitor token usage in Cloud Monitoring

**Pricing Examples:**
- Cloud Run: $0.00024/GB-second
- Agent Engine: Pay-per-request pricing
- GKE: Standard cluster costs
- Gemini API: $3.50/1M tokens (Pro)

### 📚 Reference Architecture

**Production Agent System:**
```
┌─────────────────┐
│   Load Balancer │
└────────┬────────┘
         │
    ┌────▼────┐
    │Cloud Run│ (Agent containers)
    └────┬────┘
         │
    ┌────▼──────────┐
    │ Agent Engine  │ (Orchestration)
    └────┬──────────┘
         │
    ┌────▼────────────────┐
    │  Vertex AI Search   │ (RAG)
    │  Vector Search      │
    │  Gemini 2.5 Pro     │
    └─────────────────────┘
```

### 🎯 Best Practices for Jeremy

**1. Start with Templates:**
```bash
# Use Agent Starter Pack templates
uvx agent-starter-pack create my-agent --template agentic_rag
```

**2. Local Development:**
```bash
# Test locally first
adk serve --port 8080
curl http://localhost:8080/query -d '{"question": "test"}'
```

**3. Gradual Deployment:**
```bash
# Deploy to dev → staging → prod
asp deploy --env dev
# Test thoroughly
asp deploy --env staging
# Final production push
asp deploy --env production
```

**4. Monitor Everything:**
- Enable Cloud Trace
- Set up error reporting
- Track token usage
- Monitor response times
- Set up alerting

### 📖 Official Documentation

**Core Resources:**
- ADK Docs: https://google.github.io/adk-docs/
- Agent Starter Pack: https://github.com/GoogleCloudPlatform/agent-starter-pack
- Agent Engine: https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/overview
- Agent Builder: https://cloud.google.com/products/agent-builder

**Tutorials:**
- Building AI Agents: https://codelabs.developers.google.com/devsite/codelabs/building-ai-agents-vertexai
- Multi-agent Systems: https://cloud.google.com/blog/products/ai-machine-learning/build-and-manage-multi-system-agents-with-vertex-ai

## When This Skill Activates

This skill automatically activates when you mention:
- Agent development, ADK, or Agent Starter Pack
- Multi-agent systems or orchestration
- Containerized agent deployment
- Cloud Run, GKE, or Agent Engine deployment
- RAG agents or ReAct agents
- Agent templates or scaffolding
- CI/CD for agents
- Production agent systems

## Integration with Other Services

**Google Cloud:**
- Vertex AI (Gemini, Search, Vector Search)
- Cloud Storage (data storage)
- Cloud Functions (triggers)
- Cloud Scheduler (automation)
- Cloud Logging & Monitoring

**Third-party:**
- LangChain integration
- CrewAI orchestration
- Custom tool frameworks

## Success Metrics

**Track:**
- Agent response time (target: <2s)
- Evaluation scores (target: >85% accuracy)
- Deployment frequency (target: daily)
- System uptime (target: 99.9%)
- Cost per query (target: <$0.01)

---

**This skill makes Jeremy a Google Cloud agent architecture expert with instant access to ADK, Agent Starter Pack, and production deployment patterns.**
