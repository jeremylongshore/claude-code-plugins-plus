# Google Cloud Agent SDK Master - Jeremy's Agent Architecture Powerhouse

**Comprehensive Google Cloud Agent Development Kit (ADK) and Agent Starter Pack mastery for building production-grade containerized multi-agent systems.**

[![Version](https://img.shields.io/badge/version-1.0.0-blue)](plugin.json)
[![Category](https://img.shields.io/badge/category-productivity-green)](https://github.com/jeremylongshore/claude-code-plugins)
[![Google Cloud](https://img.shields.io/badge/Google_Cloud-Agent_SDK-4285F4?logo=google-cloud)](https://google.github.io/adk-docs/)

## 🎯 Purpose

This plugin makes Claude Code an expert in Google's Agent Development Kit (ADK) and Agent Starter Pack, with automatic activation for agent creation, multi-agent orchestration, containerized deployment, and production CI/CD.

## ✨ Key Features

### 🤖 Agent Development Kit (ADK)
- Build production agents in <100 lines of Python
- Same framework powering Google Agentspace
- Model-agnostic (optimized for Gemini)
- Flexible orchestration (workflow & LLM-driven)
- Multi-agent hierarchies

### 📦 Agent Starter Pack
- 5 production-ready templates
- One-command CI/CD setup
- GitHub Actions or Cloud Build
- Multi-environment deployment
- Automated testing & evaluation

### 🚀 Deployment Targets
- **Cloud Run**: Serverless containers
- **GKE**: Full Kubernetes orchestration
- **Agent Engine**: Fully managed runtime
- **Local/Docker**: Development & testing

### 🧠 Agent Types
- **ReAct Agents**: Tool use with reasoning
- **RAG Agents**: Document retrieval & Q&A
- **Multi-Agent Systems**: Hierarchical coordination
- **Workflow Agents**: Sequential, parallel, loop
- **Custom Agents**: User-defined implementations

## 🚀 Installation

```bash
# Install the plugin
/plugin install 004-jeremy-google-cloud-agent-sdk@claude-code-plugins-plus
```

## 📋 Components

### Agent Skills (1)
- **agent-sdk-master** - Auto-activates for all ADK and agent operations

### Slash Commands (1)
- `/create-agent` - Scaffold production-ready agent projects

## 💡 Usage Examples

### Create RAG Agent
```bash
/create-agent

Agent name: docs-qa-agent
Template: agentic_rag
Deployment: cloud_run
Project: my-project
Region: us-central1
```

**Generates:**
- Complete agent project structure
- CI/CD pipelines (GitHub Actions + Cloud Build)
- Dockerfile and deployment configs
- Unit and integration tests
- README and documentation

### Build Multi-Agent System
```
"Build a multi-agent system with 3 specialized agents: researcher, analyst, and writer"
```

**Auto-activates skill and creates:**
- Orchestrator agent architecture
- Specialized sub-agent implementations
- Inter-agent communication protocols
- Deployment configuration
- Evaluation framework

### Deploy to Production
```
"Deploy this agent to Cloud Run with auto-scaling and monitoring"
```

**Auto-generates:**
- Cloud Run deployment manifest
- Terraform infrastructure code
- Monitoring dashboards
- Alert policies
- Deployment scripts

## 🔧 Technical Implementation

### Prerequisites
```bash
# Install Agent Starter Pack
pip install agent-starter-pack

# Or use ADK directly
pip install google-cloud-aiplatform[adk,agent_engines]>=1.111

# Authenticate
gcloud auth application-default login
```

### Create Agent (Quick Start)
```bash
# Using Agent Starter Pack (recommended)
uvx agent-starter-pack create my-agent \
    --template adk_base \
    --deployment cloud_run

# Navigate and deploy
cd my-agent
adk deploy --target cloud_run --region us-central1
```

### Code Example (ADK)
```python
from google.cloud.aiplatform import agent
from vertexai.preview.agents import ADKAgent

@agent.adk_agent
class MyAgent(ADKAgent):
    def __init__(self):
        super().__init__(
            model="gemini-2.5-pro",
            tools=[search_tool, code_exec_tool]
        )

    def run(self, query: str):
        return self.generate(query)
```

## 🎯 Available Templates

### 1. adk_base
**Type**: ReAct agent using ADK
**Best for**: General-purpose agents with tool use
**Includes**: Search, code execution, custom tools

### 2. agentic_rag
**Type**: Document retrieval + Q&A
**Best for**: Knowledge bases, customer support
**Includes**: Vertex AI Search, Vector Search

### 3. langgraph_base_react
**Type**: LangGraph orchestration
**Best for**: Complex workflows with state
**Includes**: State management, conditional logic

### 4. crewai_coding_crew
**Type**: Multi-agent collaboration
**Best for**: Software development, research
**Includes**: Role-based agents, task delegation

### 5. adk_live
**Type**: Multimodal RAG
**Best for**: Video/audio processing
**Includes**: Streaming support, multimodal understanding

## 🚀 Deployment Options

### Cloud Run (Serverless)
- **Scaling**: 0→N automatic
- **Pricing**: Pay-per-use
- **Timeout**: 60 minutes
- **Memory**: Up to 8GB

**Deploy:**
```bash
adk deploy --target cloud_run --region us-central1
```

### Agent Engine (Managed)
- **Runtime**: Fully managed
- **Scaling**: Automatic
- **Observability**: Built-in
- **Integration**: Native Vertex AI

**Deploy:**
```bash
asp deploy --env production --target agent_engine
```

### GKE (Kubernetes)
- **Control**: Full orchestration
- **Scaling**: Advanced policies
- **Networking**: Custom configuration
- **Resources**: Flexible allocation

**Deploy:**
```bash
kubectl apply -f deployment/k8s/
```

## 📊 Multi-Agent Orchestration

### Hierarchical Agents
```python
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

### Parallel Execution
```python
import asyncio

class ParallelAgent(ADKAgent):
    async def run_parallel(self, tasks: list[str]):
        results = await asyncio.gather(*[
            self.specialized_agent(task)
            for task in tasks
        ])
        return self.synthesize(results)
```

## 💰 Cost Optimization

**Pricing Breakdown:**
- **Cloud Run**: $0.00024/GB-second (scales to zero)
- **Agent Engine**: Pay-per-request
- **Gemini 2.5 Pro**: $3.50/1M input tokens
- **Gemini 2.5 Flash**: $0.35/1M input tokens

**Optimization Tips:**
- Use Flash for routine operations
- Cache embeddings for RAG
- Implement request batching
- Monitor token usage
- Set up budget alerts

**Typical Monthly Costs:**
- Small agent: $50-100
- Medium agent: $200-500
- Large multi-agent: $1000-2000

## 🔒 Security Best Practices

### Service Accounts
```bash
# Create minimal-permission SA
gcloud iam service-accounts create agent-sa

# Grant required permissions
gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="serviceAccount:agent-sa@PROJECT.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"
```

### Secret Management
```python
from google.cloud import secretmanager

client = secretmanager.SecretManagerServiceClient()
name = "projects/PROJECT/secrets/api-key/versions/latest"
response = client.access_secret_version(name=name)
api_key = response.payload.data.decode('UTF-8')
```

### VPC Service Controls
```bash
# Enable VPC SC
gcloud access-context-manager perimeters create agent-perimeter \
    --resources=projects/PROJECT_ID \
    --restricted-services=aiplatform.googleapis.com
```

## 📈 Monitoring & Evaluation

### Built-in Evaluation
```python
from google.cloud.aiplatform import agent_evaluation

eval_config = agent_evaluation.EvaluationConfig(
    metrics=["accuracy", "relevance", "safety"],
    test_dataset="gs://bucket/eval_data.jsonl"
)

results = agent.evaluate(eval_config)
```

### Cloud Trace Integration
```python
@traced_agent
class MonitoredAgent(ADKAgent):
    def run(self, query: str):
        with self.trace_span("retrieval"):
            docs = self.retrieve(query)
        with self.trace_span("generation"):
            response = self.generate(query, docs)
        return response
```

### Monitoring Dashboard
```bash
# Create dashboard
gcloud monitoring dashboards create \
    --config-from-file monitoring/dashboard.json
```

## 🔄 CI/CD Automation

### GitHub Actions (Auto-Generated)
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
      - name: Test
        run: pytest tests/
      - name: Deploy
        run: adk deploy --target cloud_run
```

### Cloud Build Pipeline
```yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/agent', '.']
  - name: 'gcr.io/cloud-builders/gcloud'
    args: ['run', 'deploy', 'agent', '--image=gcr.io/$PROJECT_ID/agent']
```

## 🎯 Use Cases

### 1. Customer Support Agent
- RAG over documentation
- Auto-respond to tickets
- Escalation routing

### 2. Research Assistant
- Multi-source information gathering
- Synthesis and summarization
- Citation tracking

### 3. Code Review Agent
- Analyze pull requests
- Suggest improvements
- Security scanning

### 4. Content Creation Crew
- Research → Write → Edit pipeline
- Multi-agent collaboration
- Quality assurance

## 📚 Documentation

**Official Resources:**
- [ADK Documentation](https://google.github.io/adk-docs/)
- [Agent Starter Pack GitHub](https://github.com/GoogleCloudPlatform/agent-starter-pack)
- [Agent Engine Overview](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/overview)
- [Agent Builder](https://cloud.google.com/products/agent-builder)

**Tutorials:**
- [Building AI Agents Codelab](https://codelabs.developers.google.com/devsite/codelabs/building-ai-agents-vertexai)
- [Multi-Agent Systems Blog](https://cloud.google.com/blog/products/ai-machine-learning/build-and-manage-multi-system-agents-with-vertex-ai)

## 🎓 Training Resources

**Learn:**
- Agent architecture patterns
- Multi-agent orchestration
- RAG implementation
- Production deployment
- Monitoring & evaluation

## 🎯 When This Activates

**Trigger phrases:**
- "adk", "agent development kit"
- "agent starter pack", "build agent"
- "multi-agent", "orchestration"
- "cloud run deployment", "agent engine"
- "rag agent", "react agent"

## 📈 Roadmap

**Planned features:**
- Gemini 2.5 Pro integration
- Advanced multi-agent patterns
- Real-time streaming agents
- Agentic AI frameworks
- Enterprise templates

---

**Part of [Claude Code Plugins](https://github.com/jeremylongshore/claude-code-plugins)** - 234 production-ready plugins

**Author:** Jeremy Longshore | **License:** MIT | **Version:** 1.0.0
