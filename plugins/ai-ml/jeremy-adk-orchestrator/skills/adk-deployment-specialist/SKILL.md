---
name: adk-deployment-specialist
description: |
  Deploy and orchestrate Vertex AI ADK agents using A2A protocol. Manages AgentCard discovery, task submission, Code Execution Sandbox, and Memory Bank. Use when asked to "deploy ADK agent" or "orchestrate agents". Trigger with phrases like 'deploy', 'infrastructure', or 'CI/CD'.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(cmd:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
---
# Adk Deployment Specialist

This skill provides automated assistance for adk deployment specialist tasks.

## Overview

Expert in building and deploying production multi-agent systems using Google's Agent Development Kit (ADK). Handles agent orchestration (Sequential, Parallel, Loop), A2A protocol communication, Code Execution Sandbox for GCP operations, Memory Bank for stateful conversations, and deployment to Vertex AI Agent Engine.

### Core Capabilities

1. **ADK Agent Creation**: Build agents in Python (stable), Java (0.3.0), or Go (Nov 2025)
2. **Multi-Agent Orchestration**: Sequential/Parallel/Loop agent patterns
3. **A2A Protocol Management**: Agent-to-Agent communication and task delegation
4. **Code Execution**: Secure sandbox for running gcloud commands and Python/Go code
5. **Memory Bank**: Persistent conversation memory across sessions (14-day TTL)
6. **Production Deployment**: One-command deployment with `adk deploy`
7. **Observability**: Agent Engine UI dashboards, token tracking, error monitoring

## Prerequisites

- A Google Cloud project with Vertex AI enabled (and permissions to deploy Agent Engine runtimes)
- ADK installed (and pinned to the project’s supported version)
- A clear agent contract: tools required, orchestration pattern, and deployment target (local vs Agent Engine)
- A plan for secrets/credentials (OIDC/WIF where possible; never commit long-lived keys)

## Instructions

1. Confirm the desired architecture (single agent vs multi-agent) and orchestration pattern (Sequential/Parallel/Loop).
2. Define the AgentCard + A2A interfaces (inputs/outputs, task submission, and status polling expectations).
3. Implement the agent(s) with the minimum required tool surface (Code Execution Sandbox and/or Memory Bank as needed).
4. Test locally with representative prompts and failure cases, then add smoke tests for deployment verification.
5. Deploy to Vertex AI Agent Engine and validate the generated endpoints (`/.well-known/agent-card`, task send/status APIs).
6. Add observability: logs, dashboards, and retry/backoff behavior for transient failures.

## Output

- Agent source files (or patches) ready for deployment
- Deployment commands/config (e.g., `adk deploy` invocation + required flags)
- A verification checklist for Agent Engine endpoints (AgentCard + task APIs) and security posture

## Error Handling

- Deployment failures: provide the exact failing command, logs to inspect, and the minimal change to unblock
- Auth/permission issues: identify the missing role/API and suggest least-privilege remediation
- Orchestration failures: isolate which agent step failed and provide a retry-safe plan

## Examples

- “Deploy this ADK multi-agent supervisor to Agent Engine with Code Execution and Memory Bank enabled.”
- “Expose an A2A AgentCard and implement `/v1/tasks:send` + polling for long-running tasks.”

## Resources

- ADK docs: https://cloud.google.com/vertex-ai/docs/agent-engine
- Workload Identity (CI/CD): https://cloud.google.com/iam/docs/workload-identity-federation
- A2A / AgentCard patterns: see `000-docs/6767-a-SPEC-DR-STND-claude-code-plugins-standard.md`

## When This Skill Activates

### Trigger Phrases
- "Deploy ADK agent to Agent Engine"
- "Create multi-agent system with ADK"
- "Implement A2A protocol"
- "Use Code Execution Sandbox"
- "Set up Memory Bank for agent"
- "Orchestrate multiple agents"
- "Build ADK agent in Python/Java/Go"
- "Deploy to Vertex AI Agent Engine"

### Use Case Patterns
- Building GCP deployment automation agents
- Creating RAG agents with LangChain integration
- Orchestrating Genkit flows with ADK supervisors
- Implementing stateful conversational agents
- Deploying secure code execution environments

## How It Works

### Phase 1: Agent Architecture Design

```
User Request → Analyze:
- Single agent vs multi-agent system?
- Tools needed (Code Exec, Memory Bank, custom tools)?
- Orchestration pattern (Sequential, Parallel, Loop)?
- Integration with LangChain/Genkit?
- Deployment target (local, Agent Engine, Cloud Run)?
```

### Phase 2: ADK Agent Implementation

**Simple Agent (Python)**:
```python
from google import adk

# Define agent with tools
agent = adk.Agent(
    model="gemini-2.5-flash",
    tools=[
        adk.tools.CodeExecution(),  # Secure sandbox
        adk.tools.MemoryBank(),     # Persistent memory
    ],
    system_instruction="""
You are a GCP deployment specialist.
Help users deploy resources securely using gcloud commands.
    """
)

# Run agent
response = agent.run("Deploy a GKE cluster named prod in us-central1")
print(response)
```

**Multi-Agent Orchestrator (Python)**:
```python
from google import adk

# Define specialized sub-agents
validator_agent = adk.Agent(
    model="gemini-2.5-flash",
    system_instruction="Validate GCP configurations"
)

deployer_agent = adk.Agent(
    model="gemini-2.5-flash",
    tools=[adk.tools.CodeExecution()],
    system_instruction="Deploy validated GCP resources"
)

monitor_agent = adk.Agent(
    model="gemini-2.5-flash",
    system_instruction="Monitor deployment status"
)

# Orchestrate with Sequential pattern
orchestrator = adk.SequentialAgent(
    agents=[validator_agent, deployer_agent, monitor_agent],
    system_instruction="Coordinate validation → deployment → monitoring"
)

result = orchestrator.run("Deploy a production GKE cluster")
```

### Phase 3: Code Execution Integration

The Code Execution Sandbox provides:
- **Security**: Isolated environment, no access to your system
- **State Persistence**: 14-day memory, configurable TTL
- **Stateful Sessions**: Builds on previous executions

```python
# Agent with Code Execution
agent = adk.Agent(
    model="gemini-2.5-flash",
    tools=[adk.tools.CodeExecution()],
    system_instruction="""
Execute gcloud commands in the secure sandbox.
Remember previous operations in this session.
    """
)

# Turn 1: Create cluster
agent.run("Create GKE cluster named dev-cluster with 3 nodes")
# Sandbox executes: gcloud container clusters create dev-cluster --num-nodes=3

# Turn 2: Deploy to cluster (remembers cluster from Turn 1)
agent.run("Deploy my-app:latest to that cluster")
# Sandbox remembers dev-cluster, executes kubectl commands
```

### Phase 4: Memory Bank Integration

Persistent conversation memory across sessions:

```python
agent = adk.Agent(
    model="gemini-2.5-flash",
    tools=[adk.tools.MemoryBank()],
    system_instruction="Remember user preferences and project context"
)

# Session 1 (Monday)
agent.run("I prefer deploying to us-central1 region", session_id="user-123")

# Session 2 (Wednesday) - same session_id
agent.run("Deploy a Cloud Run service", session_id="user-123")
# Agent remembers: uses us-central1 automatically
```

### Phase 5: A2A Protocol Deployment

Deploy agent to Agent Engine with A2A endpoint:

```bash
# Install ADK
pip install google-adk

# Deploy with one command
adk deploy \
  --agent-file agent.py \
  --project-id my-project \
  --region us-central1 \
  --service-name gcp-deployer-agent
```

Agent Engine creates:
- **A2A Endpoint**: `https://gcp-deployer-agent-{hash}.run.app`
- **AgentCard**: `/.well-known/agent-card` metadata
- **Task API**: `/v1/tasks:send` for task submission
- **Status API**: `/v1/tasks/{task_id}` for polling

### Phase 6: Calling from Claude

Once deployed, Claude can invoke via A2A protocol:

```python
# In Claude Code plugin / external script
import requests

def invoke_adk_agent(message, session_id=None):
    """
    Call deployed ADK agent via A2A protocol.
    """
    response = requests.post(
        "https://gcp-deployer-agent-xyz.run.app/v1/tasks:send",
        json={
            "message": message,
            "session_id": session_id or "claude-session-123",
            "config": {
                "enable_code_execution": True,
                "enable_memory_bank": True,
            }
        },
        headers={"Authorization": f"Bearer {get_token()}"}
    )

    return response.json()

# Use from Claude
result = invoke_adk_agent("Deploy GKE cluster named prod-api")
```

## Workflow Examples

### Example 1: GCP Deployment Agent

**User**: "Create an ADK agent that deploys GCP resources"

**Implementation**:
```python
from google import adk

deployment_agent = adk.Agent(
    model="gemini-2.5-flash",
    tools=[
        adk.tools.CodeExecution(),
        adk.tools.MemoryBank(),
    ],
    system_instruction="""
You are a GCP deployment specialist.

CAPABILITIES:
- Deploy GKE clusters
- Deploy Cloud Run services
- Deploy Vertex AI Pipelines
- Manage IAM permissions
- Monitor deployments

SECURITY:
- Validate all configurations before deployment
- Use least-privilege IAM
- Log all operations
- Never expose credentials
    """
)

# Deploy to Agent Engine
# $ adk deploy --agent-file deployment_agent.py --service-name gcp-deployer
```

### Example 2: Multi-Agent RAG System

**User**: "Build a RAG system with ADK orchestrating a LangChain retriever"

**Implementation**:
```python
from google import adk
from langchain.retrievers import VertexAISearchRetriever

# Sub-Agent 1: LangChain RAG
class RAGAgent(adk.Agent):
    def __init__(self):
        self.retriever = VertexAISearchRetriever(...)
        super().__init__(model="gemini-2.5-flash")

    def retrieve_docs(self, query):
        return self.retriever.get_relevant_documents(query)

# Sub-Agent 2: ADK Answer Generator
answer_agent = adk.Agent(
    model="gemini-2.5-pro",  # More powerful for final answer
    system_instruction="Generate comprehensive answers from retrieved docs"
)

# Orchestrator
orchestrator = adk.SequentialAgent(
    agents=[RAGAgent(), answer_agent],
    system_instruction="First retrieve docs, then generate answer"
)
```

### Example 3: Async Deployment with Status Polling

**User**: "Deploy a GKE cluster and monitor progress"

**Implementation**:
```python
# Submit async task
task_response = invoke_adk_agent(
    "Deploy GKE cluster named prod-api with 5 nodes in us-central1"
)

task_id = task_response["task_id"]
print(f"✅ Task submitted: {task_id}")

# Poll for status
import time
while True:
    status = requests.get(
        f"https://gcp-deployer-agent-xyz.run.app/v1/tasks/{task_id}",
        headers={"Authorization": f"Bearer {get_token()}"}
    ).json()

    if status["status"] == "SUCCESS":
        print(f"✅ Cluster deployed!")
        break
    elif status["status"] == "FAILURE":
        print(f"❌ Deployment failed: {status['error']}")
        break
    else:
        print(f"⏳ Status: {status['status']} ({status.get('progress', 0)*100}%)")
        time.sleep(10)
```

## Production Best Practices

1. **Agent Identities**: ADK agents get Native Agent Identities (IAM principals)
2. **Least Privilege**: Grant minimum required permissions
3. **VPC Service Controls**: Enable for enterprise security
4. **Model Armor**: Protects against prompt injection
5. **Session Management**: Use consistent session_ids for Memory Bank
6. **Error Handling**: Implement retries with exponential backoff
7. **Observability**: Monitor via Agent Engine UI dashboard

## Tool Permissions

- **Read**: Analyze existing agent code
- **Write**: Create new agent files
- **Edit**: Modify agent configurations
- **Grep**: Find integration points
- **Glob**: Locate related files
- **Bash**: Install ADK, deploy agents, run tests

## Integration Patterns

### ADK + Genkit
```python
# Use Genkit for flows, ADK for orchestration
genkit_flow_agent = create_genkit_flow()
orchestrator = adk.SequentialAgent(
    agents=[validator, genkit_flow_agent, monitor]
)
```

### ADK + LangChain
```python
# LangChain for RAG, ADK for multi-agent coordination
langchain_rag = create_langchain_retriever()
orchestrator = adk.ParallelAgent(
    agents=[langchain_rag, fact_checker, answer_generator]
)
```

## Deployment Commands

```bash
# Install ADK
pip install google-adk  # Python
go get google.golang.org/adk  # Go

# Deploy to Agent Engine
adk deploy \
  --agent-file my_agent.py \
  --project-id my-project \
  --region us-central1 \
  --service-name my-agent

# Deploy to Cloud Run (custom)
gcloud run deploy my-agent \
  --source . \
  --region us-central1

# Deploy locally for testing
adk run --agent-file my_agent.py
```

## Version History

- **1.0.0** (2025): ADK Preview with Python/Java/Go support, Agent Engine GA, Code Execution Sandbox, Memory Bank

## References

- ADK Docs: https://google.github.io/adk-docs/
- A2A Protocol: https://google.github.io/adk-docs/a2a/
- Agent Engine: https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/overview
- Code Execution: https://cloud.google.com/agent-builder/agent-engine/code-execution/overview
- Memory Bank: https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/memory-bank/overview
