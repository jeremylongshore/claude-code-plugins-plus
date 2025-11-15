# Supplemental Reference: ADK & Vertex AI Agent Engine

**Created:** November 13, 2025
**Purpose:** Consolidated reference documentation for Agent Development Kit and Vertex AI Agent Engine
**Sources:** Official Google Cloud documentation

---

## Agent Development Kit (ADK) Overview

### What is ADK?

Agent Development Kit is a **flexible and modular framework** for developing and deploying AI agents. Designed to "make agent development feel more like software development," it's:

- **Model-agnostic**: Works with any LLM, though optimized for Gemini
- **Deployment-agnostic**: Deploy locally, on Vertex AI, Cloud Run, or GKE
- **Developer-friendly**: Systematic evaluation and security-focused design

### Core Components

#### 1. Agent Types

- **LLM Agents**: AI-powered agents with dynamic routing capabilities
- **Workflow Agents**:
  - Sequential workflows
  - Parallel execution
  - Loop-based iterations
- **Custom Agents**: Build specialized agents for specific use cases
- **Multi-Agent Systems**: Orchestrate multiple agents working together

#### 2. Tools & Capabilities

**Built-in Tools:**
- Google Search integration
- Code Execution sandbox
- Memory Bank operations (PreloadMemory, LoadMemory)

**Custom Function Tools:**
- Wrap any Python function as an agent tool
- Automatic schema inference from docstrings
- Type-safe parameter validation

**Third-Party Integrations:**
- Tavily (web search)
- Firecrawl (web scraping)
- Exa (semantic search)
- Other agents as callable tools

#### 3. Sessions & State Management

**Session Management:**
- Track multi-turn conversations
- Persist conversation history
- Associate sessions with specific users

**State Persistence:**
- `InMemorySessionService` (development/testing)
- `DatabaseSessionService` (SQL databases: SQLite, MySQL, PostgreSQL)
- `VertexAiSessionService` (production-ready, fully managed)

**Memory Systems:**
- Short-term memory via Sessions
- Long-term memory via Memory Bank
- Context caching for efficiency
- Automatic context compression

#### 4. Runtime & Deployment Options

**Local Execution:**
```bash
pip install google-adk
python agent.py
```

**Vertex AI Agent Engine:**
- Fully managed serverless platform
- Automatic scaling
- Enterprise security (VPC-SC, IAM)
- Integrated monitoring

**Cloud Run:**
```bash
adk deploy cloud_run --project PROJECT_ID --region REGION
```

**Google Kubernetes Engine (GKE):**
- Full Kubernetes control
- Custom resource allocation
- Advanced networking

### Installation

**Python:**
```bash
pip install google-adk
```

**Go & Java:**
Available via respective package managers (check official docs)

### Key Differentiator

ADK bridges **traditional workflow automation** and **autonomous agent capabilities** by providing:
- Predictable, deterministic pipelines (Workflow agents)
- Adaptive, LLM-driven behavior (LLM agents)
- Flexible orchestration layer for both approaches

---

## Vertex AI Agent Engine Overview

### What It Is

**Vertex AI Agent Engine** is a managed platform within Vertex AI that enables developers to **deploy, manage, and scale AI agents in production**. It's a comprehensive "set of services" providing enterprise-grade infrastructure for agent applications.

### Core Services

#### 1. Runtime Platform

**Features:**
- Deploy and scale agents with managed infrastructure
- Automatic horizontal scaling based on load
- Security compliance (VPC-SC, IAM integration)
- Access to Gemini models with function calling
- Private endpoints and custom networking

**Deployment Methods:**
- Agent Starter Pack (production templates with Terraform)
- Manual deployment (five-step workflow)
- SDK-based deployment (Python, Go, Java)

#### 2. Quality & Evaluation

**Gen AI Evaluation Integration:**
- Assess agent performance systematically
- Track quality metrics over time
- A/B testing capabilities
- Automated testing pipelines

#### 3. Example Store

**Dynamic Few-Shot Learning:**
- Store and retrieve example prompts/responses
- Enhance agent capabilities with context-specific examples
- Improve model performance on specialized tasks
- Version-controlled example management

#### 4. Sessions Service

**Conversation Management:**
- Store individual user-agent interactions
- Maintain conversation context across turns
- Associate sessions with authenticated users
- Session lifecycle management

**Integration:**
```python
from google.adk.sessions import VertexAiSessionService

session_service = VertexAiSessionService(
    project=PROJECT_ID,
    location=LOCATION,
    agent_engine_id=agent_engine_id
)
```

#### 5. Memory Bank

**Long-Term Memory:**
- Persist information across sessions
- User-specific memory isolation
- Automatic memory generation from conversations
- Similarity-based memory retrieval
- Memory expiration via TTL settings

**Use Cases:**
- User preferences and settings
- Historical interaction patterns
- Personalization across sessions
- Knowledge accumulation

#### 6. Code Execution Sandbox

**Secure Code Runtime:**
- Isolated sandbox environments
- Support for Python code execution
- Package installation capabilities
- Timeout and resource limits

### Supported Frameworks

#### Full Integration (Tier 1)
- **LangChain**: Full chain compatibility
- **LangGraph**: Graph-based workflows
- **Agent Development Kit (ADK)**: Native integration

#### SDK Integration (Tier 2)
- **AG2**: Multi-agent conversations
- **LlamaIndex**: RAG applications

#### Custom Templates (Tier 3)
- **CrewAI**: Role-based multi-agent systems
- **Custom Frameworks**: Bring your own agent framework

### Deployment Paths

#### Agent Starter Pack (Recommended)

**What You Get:**
- Production-ready agent templates
- Interactive playground for testing
- Automated infrastructure via Terraform
- CI/CD pipelines (GitHub Actions)
- Best practices baked in

**Quick Start:**
```bash
# Clone starter pack
git clone https://github.com/GoogleCloudPlatform/agent-starter-pack

# Deploy with Terraform
cd terraform/
terraform init
terraform apply
```

#### Manual Deployment

**Five-Step Workflow:**

1. **Environment Setup**: GCP project, APIs, credentials
2. **Agent Development**: Build agent using ADK, LangChain, or custom code
3. **Deployment**: Package and deploy to Agent Engine
4. **Usage**: Query agent via SDK, REST API, or A2A protocol
5. **Management**: Monitor, scale, update agents

### Enterprise Security Features

#### VPC Service Controls
- Perimeter-based security
- Data exfiltration protection
- Approved resource access only

#### Private Service Connections
- Private endpoints for agents
- No public internet exposure
- Custom VPC networking

#### Encryption & Compliance
- Customer-managed encryption keys (CMEK)
- Data residency compliance
- HIPAA workload support
- Access transparency logging

### Key Use Cases

#### Financial Services
- Currency conversion via public APIs
- Real-time exchange rate queries
- Financial data aggregation

#### Geospatial Applications
- Solar project site identification using Google Maps
- Location-based recommendations
- Geographic data analysis

#### Database Integration
- RAG applications with AlloyDB
- Cloud SQL query agents
- MongoDB Atlas integration
- Graph database queries
- Vector database similarity search

#### Multi-Agent Systems
- A2A protocol-based agent collaboration
- Supervisory orchestration patterns
- Distributed agent architectures

---

## Memory Bank Deep Dive

### What It Is

Memory Bank enables **dynamic generation of long-term, personalized memories** from user conversations with agents. It provides:

> "Long-term memories are personalized information that can be accessed across multiple sessions for a particular user."

### Architecture

**Scope-Based Isolation:**
- Each memory collection is isolated by **agent + user combination**
- No cross-user memory access
- No cross-agent memory leakage
- Identity-scoped data security

**Memory Structure:**
- Self-contained information pieces
- Contextually relevant snippets
- Expandable agent context
- Revision history tracking

### Core Operations

#### Memory Generation

**Extraction Process:**
1. Analyze source conversation data
2. Extract meaningful, actionable information
3. Consolidate with existing memories (deduplication, merging)
4. Store in persistent, managed storage

**Key Features:**
- **Asynchronous operation**: Agents don't wait for memory generation
- **Multimodal understanding**: Process images, audio, and text
- **Intelligent consolidation**: Merge related memories automatically

**Example:**
```python
# After agent turn, automatically save to Memory Bank
async def add_session_to_memory(callback_context: CallbackContext):
    if invocation_context.memory_service:
        await invocation_context.memory_service.add_session_to_memory(
            invocation_context.session
        )
```

#### Storage & Retrieval

**Storage Characteristics:**
- **Persistent**: Survives agent restarts and redeployments
- **Managed**: Fully handled by Google Cloud infrastructure
- **Isolated**: Identity-scoped per user and agent
- **Versioned**: Track memory revisions over time

**Retrieval Methods:**
- **Similarity search**: Find contextually relevant memories
- **Time-based filtering**: Retrieve recent or historical memories
- **Explicit queries**: Search by keywords or semantic meaning

**TTL Management:**
- Set automatic expiration for memories
- Clean up stale or outdated information
- Comply with data retention policies

#### Integration with ADK

**VertexAiMemoryBankService:**
```python
from google.adk.memory import VertexAiMemoryBankService

memory_service = VertexAiMemoryBankService(
    project=PROJECT_ID,
    location=LOCATION,
    agent_engine_id=agent_engine_id
)

# Use in Runner
runner = Runner(
    app_name=agent.name,
    agent=agent,
    session_service=session_service,
    memory_service=memory_service,  # ← Long-term memory
)
```

**Built-in ADK Tools:**

1. **PreloadMemoryTool** (automatic):
   - Retrieves memories at the beginning of every agent turn
   - Appends to System Instructions automatically
   - No explicit agent call required

2. **LoadMemoryTool** (on-demand):
   - Agent decides when to load memories
   - Explicit tool call based on conversation context
   - More control over memory retrieval

**Example Agent with Memory:**
```python
from google.adk.agents import Agent
from google.adk.tools.preload_memory_tool import PreloadMemoryTool

agent = Agent(
    name="weather_agent",
    model="gemini-2.5-flash",
    tools=[
        get_weather,
        PreloadMemoryTool()  # ← Automatically loads memories
    ],
    after_agent_callback=add_session_to_memory  # ← Saves memories
)
```

### Use Cases

#### Long-Term Personalization
- Remember user preferences across sessions
- Track evolving user interests
- Maintain consistent personality

#### LLM-Driven Knowledge Extraction
- Automatically identify important information
- Build user-specific knowledge graphs
- Extract structured data from conversations

#### Dynamic Evolving Context
- Adapt to changing user needs
- Learn from historical interactions
- Improve responses over time

### Memory Generation Behavior

**Not All Conversations Generate Memories:**
- Only **meaningful** information is persisted
- Transactional queries don't create memories
- LLM decides what's worth remembering

**Example:**
```
User: "What's the weather in New York?"
→ No memory generated (transactional query)

User: "Whenever asked about Seattle weather, say it's raining as usual."
→ Memory generated: "User preference for Seattle weather responses"

Next session:
User: "What's the weather in Seattle?"
→ Agent retrieves memory and responds: "It's raining as usual in Seattle."
```

---

## Related jeremy-* Plugins

### jeremy-adk-orchestrator
- ADK supervisory orchestration with A2A protocol support
- Multi-agent system management
- Memory Bank integration patterns

### jeremy-vertex-engine
- Agent Engine inspection and deployment
- Runtime configuration validation
- A2A protocol compliance checking

### jeremy-vertex-validator
- Production readiness validation
- Agent Engine health checks
- Memory Bank configuration verification

### jeremy-genkit-pro
- Firebase Genkit integration with ADK
- Cloud Run deployment automation
- Gemini model integration

### jeremy-vertex-terraform
- Terraform infrastructure for Vertex AI services
- Agent Engine resource provisioning
- Automated deployment pipelines

---

## Quick Reference

### ADK Installation
```bash
pip install google-adk
```

### Agent Engine Resource Name Format
```
projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{REASONING_ENGINE_ID}
```

### Session Service URI
```
agentengine://{AGENT_ENGINE_ID}
```

### Memory Bank Console URL
```
https://console.cloud.google.com/vertex-ai/agents/locations/{LOCATION}/agent-engines/{AGENT_ENGINE_ID}/memories?project={PROJECT_ID}
```

### Deploy ADK Agent to Cloud Run
```bash
adk deploy cloud_run --project PROJECT_ID --region REGION \
    --service_name SERVICE_NAME \
    --session_service_uri=agentengine://AGENT_ENGINE_ID \
    --memory_service_uri=agentengine://AGENT_ENGINE_ID \
    --app_name AGENT_NAME \
    --with_ui
```

---

**Documentation Version:** November 2025
**Last Updated:** 2025-11-13
**Status:** Production-Ready Reference
