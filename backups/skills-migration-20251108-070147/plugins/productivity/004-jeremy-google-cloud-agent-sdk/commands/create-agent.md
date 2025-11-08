---
name: create-agent
description: Create a production-ready Google Cloud agent using ADK and Agent Starter Pack with CI/CD, deployment, and testing infrastructure
model: sonnet
---

# Create Production-Ready Google Cloud Agent

Scaffold a complete agent project using Google's Agent Development Kit (ADK) and Agent Starter Pack with production-ready infrastructure.

## What This Does

1. **Choose Agent Template**: Select from 5 production templates
2. **Configure Deployment**: Select deployment target (Cloud Run, GKE, Agent Engine)
3. **Generate Project**: Create complete project structure with CI/CD
4. **Setup Instructions**: Provide step-by-step deployment guide

## Available Templates

### 1. adk_base (ReAct Agent)
**Best for**: General-purpose agents with tool use
**Includes**: Search, code execution, custom tools
**Use case**: Q&A agents, research assistants, task automation

### 2. agentic_rag (RAG Agent)
**Best for**: Document-based Q&A
**Includes**: Vertex AI Search, Vector Search integration
**Use case**: Knowledge bases, documentation agents, customer support

### 3. langgraph_base_react (LangGraph)
**Best for**: Complex workflows with state management
**Includes**: LangGraph orchestration, custom nodes
**Use case**: Multi-step processes, conditional logic, state tracking

### 4. crewai_coding_crew (Multi-Agent)
**Best for**: Collaborative multi-agent systems
**Includes**: Specialized agents, role-based coordination
**Use case**: Software development, research teams, content creation

### 5. adk_live (Multimodal RAG)
**Best for**: Audio/video/text processing
**Includes**: Multimodal understanding, live streaming
**Use case**: Video analysis, audio transcription, media processing

## Deployment Targets

### Cloud Run (Serverless)
**Pros:**
- Automatic scaling 0→N
- Pay-per-use pricing
- Fast deployment
- Custom domains

**Cons:**
- 60-minute timeout
- Limited memory (8GB max)

**Best for:** Web-facing agents, APIs, low-traffic services

### Agent Engine (Managed)
**Pros:**
- Fully managed runtime
- Built-in observability
- Auto-scaling
- Integrated with Vertex AI

**Cons:**
- Vertex AI pricing
- Less customization

**Best for:** Production agents, high-scale deployment

### GKE (Kubernetes)
**Pros:**
- Full control
- Advanced networking
- Resource management
- Multi-cluster

**Cons:**
- Higher complexity
- Cluster management overhead

**Best for:** Complex multi-agent systems, enterprise deployment

## Usage

```bash
/create-agent
```

Then provide:
- Agent name
- Template choice
- Deployment target
- GCP project ID
- Region preference

## Example Workflow

**Input:**
```
Agent name: customer-support-agent
Template: agentic_rag
Deployment: cloud_run
Project: my-gcp-project
Region: us-central1
```

**Generated Structure:**
```
customer-support-agent/
├── src/
│   ├── agent.py              # Main agent implementation
│   ├── tools/
│   │   ├── search_tool.py
│   │   └── custom_tools.py
│   ├── config.py             # Configuration
│   └── prompts/
│       └── system_prompt.txt
├── deployment/
│   ├── Dockerfile
│   ├── cloudbuild.yaml
│   ├── cloud-run.yaml
│   └── terraform/
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
├── tests/
│   ├── unit/
│   │   ├── test_agent.py
│   │   └── test_tools.py
│   └── integration/
│       └── test_e2e.py
├── .github/workflows/
│   ├── test.yaml             # CI testing
│   └── deploy.yaml           # CD deployment
├── requirements.txt
├── pyproject.toml
├── README.md
└── .env.example
```

## Step-by-Step Deployment

### 1. Install Dependencies
```bash
cd customer-support-agent
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure GCP
```bash
# Authenticate
gcloud auth login
gcloud config set project my-gcp-project

# Enable APIs
gcloud services enable \
    aiplatform.googleapis.com \
    run.googleapis.com \
    cloudbuild.googleapis.com
```

### 3. Set Up Environment
```bash
# Copy example env
cp .env.example .env

# Edit with your values
vim .env
```

**Required variables:**
```env
GOOGLE_CLOUD_PROJECT=my-gcp-project
GOOGLE_CLOUD_REGION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
VERTEX_AI_SEARCH_DATASTORE=datastore-id
```

### 4. Test Locally
```bash
# Run agent locally
python src/agent.py

# Or use ADK CLI
adk serve --port 8080

# Test endpoint
curl http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What are your support hours?"}'
```

### 5. Run Tests
```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# Coverage report
pytest --cov=src tests/
```

### 6. Deploy to Cloud Run
```bash
# Using ADK CLI (recommended)
adk deploy \
    --target cloud_run \
    --region us-central1 \
    --allow-unauthenticated

# Or using gcloud
gcloud run deploy customer-support-agent \
    --source . \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300s
```

### 7. Setup CI/CD
```bash
# Connect GitHub repo
gh repo create customer-support-agent --public
git init
git add .
git commit -m "Initial agent setup"
git branch -M main
git remote add origin https://github.com/USER/customer-support-agent.git
git push -u origin main

# GitHub Actions automatically trigger on push
```

### 8. Monitor Deployment
```bash
# View logs
gcloud run services logs read customer-support-agent \
    --region us-central1 \
    --limit 100 \
    --format json

# Check metrics
gcloud monitoring dashboards create \
    --config-from-file monitoring/dashboard.json
```

## Advanced Features

### RAG Integration
```python
# Automatically included in agentic_rag template
from vertexai.preview.rag import VectorSearchTool

vector_search = VectorSearchTool(
    index_endpoint="projects/PROJECT/locations/REGION/indexEndpoints/INDEX",
    deployed_index_id="deployed_index"
)

agent.add_tool(vector_search)
```

### Multi-Agent Orchestration
```python
# Automatically included in crewai_coding_crew template
from crewai import Agent, Task, Crew

researcher = Agent(
    role="Researcher",
    goal="Research technical topics",
    tools=[search_tool]
)

writer = Agent(
    role="Writer",
    goal="Write documentation",
    tools=[write_tool]
)

crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, write_task]
)
```

### Custom Tools
```python
# Add custom tools to any agent
from vertexai.preview.agents import FunctionTool

@FunctionTool
def check_inventory(product_id: str) -> dict:
    """Check product inventory levels"""
    # Your custom logic
    return {"in_stock": True, "quantity": 42}

agent.add_tool(check_inventory)
```

## Cost Estimation

**Development:**
- Local testing: Free
- CI/CD (GitHub Actions): Free (2000 min/month)

**Production (Cloud Run):**
- Idle: $0 (scales to zero)
- Active: ~$0.10/hour at moderate load
- Gemini API: $3.50/1M tokens

**Monthly estimate for typical agent:**
- Infrastructure: $50-100
- AI API costs: $100-300
- Total: $150-400/month

## Troubleshooting

### Common Issues

**1. Authentication Errors**
```bash
# Fix: Set credentials
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
gcloud auth application-default login
```

**2. Timeout Errors**
```bash
# Fix: Increase Cloud Run timeout
gcloud run services update customer-support-agent \
    --timeout 300s
```

**3. Memory Issues**
```bash
# Fix: Increase memory
gcloud run services update customer-support-agent \
    --memory 4Gi
```

**4. Rate Limiting**
```bash
# Fix: Implement exponential backoff
# Code automatically included in templates
```

## Next Steps

After deployment:
1. **Add custom tools** for your use case
2. **Configure RAG data sources** (if using agentic_rag)
3. **Set up monitoring alerts**
4. **Implement evaluation metrics**
5. **Scale based on traffic**

## Resources

**Documentation:**
- ADK Quickstart: https://google.github.io/adk-docs/
- Agent Starter Pack: https://github.com/GoogleCloudPlatform/agent-starter-pack
- Cloud Run Docs: https://cloud.google.com/run/docs

**Examples:**
- Agent Gallery: https://cloud.google.com/vertex-ai/generative-ai/docs/samples
- GitHub Samples: https://github.com/GoogleCloudPlatform/generative-ai

---

**This command scaffolds production-ready agent projects in <5 minutes with full CI/CD, testing, and deployment automation.**
