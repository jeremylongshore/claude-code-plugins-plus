<!-- doc-class: record -->

# ADK Plugin Architecture Patterns

**Document ID**: 090-AT-ADEC-adk-plugin-architecture-patterns
**Category**: Architecture & Technical (AT)
**Type**: Architecture Decision Record (ADEC)
**Created**: 2025-11-19
**Author**: Jeremy Longshore
**Status**: Approved

---

## Executive Summary

This document establishes the canonical architecture patterns for creating production-ready Google ADK (Agent Development Kit) plugins within the Claude Code Plugins ecosystem. These patterns enable the transformation of instruction-based plugins into executable Python agents deployable on Vertex AI Engine with full A2A protocol support.

---

## Context & Background

### Problem Statement

The existing jeremy-* plugins are instruction-based (markdown templates) that rely on Claude's interpretation. While functional, they cannot:
- Deploy to Vertex AI Engine
- Participate in A2A protocol
- Execute Python code directly
- Manage persistent state
- Scale independently

### Solution Approach

Transform plugins to follow Google ADK patterns with:
- Executable Python agents using ADK SDK
- A2A protocol implementation
- Vertex AI deployment configuration
- Dual memory architecture (Session + Memory Bank)
- Production monitoring and compliance

---

## ADK Plugin Architecture

### 1. Directory Structure

```
plugin-name/
├── .claude-plugin/
│   └── plugin.json              # Plugin metadata (existing)
├── agent/                        # NEW: Python ADK agent
│   ├── __init__.py              # Module exports
│   ├── agent.py                 # Core agent with get_agent() and create_runner()
│   ├── tools.py                 # FunctionTool implementations
│   ├── system-prompt.md         # Agent instructions
│   ├── agent_card.yaml          # A2A protocol discovery
│   ├── requirements.txt         # Python dependencies
│   ├── deploy.yaml              # Vertex AI deployment config
│   └── .env.example             # Environment template
├── agents/                       # Existing instruction agents
├── commands/                     # Existing slash commands
├── skills/                       # Existing Agent Skills (2025 schema)
├── hooks/                        # Event-driven automation
├── examples/                     # Code examples
├── tests/                        # Unit tests
├── terraform/                    # IaC if applicable
├── monitoring/                   # Dashboards and alerts
├── README.md                     # Documentation
└── LICENSE                       # Apache 2.0

```

### 2. Core Components

#### 2.1 agent.py Pattern

```python
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from google.adk.runners import Runner
from google.adk.sessions import VertexAiSessionService
from google.adk.memory import VertexAiMemoryBankService

def get_agent() -> LlmAgent:
    """Returns configured agent for this plugin."""
    return LlmAgent(
        name="agent-name",
        model="models/gemini-2.0-flash-exp",
        description="Agent description",
        instruction=open("system-prompt.md").read(),
        tools=[
            FunctionTool(tool_function_1),
            FunctionTool(tool_function_2),
        ],
        enable_parallel_tool_calls=True,
        enable_code_execution=True
    )

async def create_runner() -> Runner:
    """Creates runner with dual memory architecture."""
    return Runner(
        app_name="agent-name",
        agent=get_agent(),
        session_service=VertexAiSessionService(...),
        memory_service=VertexAiMemoryBankService(...),
        callbacks={"after_session": auto_save_session_to_memory}
    )

# Export for ADK CLI
root_agent = get_agent()
```

#### 2.2 FunctionTool Pattern

```python
from typing import Dict, Any, Optional
from pydantic import BaseModel

class ToolInput(BaseModel):
    """Structured input for tool."""
    param1: str
    param2: Optional[int] = None

async def my_tool(
    input_data: ToolInput,
    tool_context: Optional[ToolContext] = None
) -> Dict[str, Any]:
    """Tool implementation with proper typing.

    Args:
        input_data: Validated input model
        tool_context: Optional ADK context

    Returns:
        Structured response dictionary
    """
    # Implementation
    return {"status": "success", "result": {...}}
```

#### 2.3 A2A Protocol Pattern

```yaml
# agent_card.yaml
name: agent-name
description: Agent description
version: 1.0.0
url: https://agent-engine.googleapis.com/v1/agents/agent-name

capabilities:
  a2a_protocol: true
  multi_agent: true
  session_management: true

skills:
  - id: skill-1
    name: Skill Name
    description: What this skill does
    input_modes: ["application/json"]
    output_modes: ["application/json"]
    tags: ["tag1", "tag2"]

security_schemes:
  bearer:
    type: http
    scheme: bearer
```

---

## Implementation Patterns

### Pattern 1: Agent Discovery

```python
async def discover_agents(
    registry_url: str = None,
    filter_capabilities: List[str] = None
) -> Dict[str, Any]:
    """Discovers agents via A2A protocol."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{registry_url}/agents")
        agents = response.json()

        # Filter by capabilities
        if filter_capabilities:
            agents = [a for a in agents
                     if any(c in a["capabilities"]
                           for c in filter_capabilities)]

        return {"agents": agents, "count": len(agents)}
```

### Pattern 2: Agent Invocation

```python
async def invoke_agent(
    agent_name: str,
    input_data: Dict[str, Any],
    session_id: str = None
) -> Dict[str, Any]:
    """Invokes agent via A2A protocol."""
    request = {
        "jsonrpc": "2.0",
        "method": "agent.invoke",
        "params": {
            "input": input_data,
            "session_id": session_id
        },
        "id": str(uuid.uuid4())
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{agent_url}/a2a",
            json=request,
            timeout=30
        )
        return response.json()
```

### Pattern 3: Session Management

```python
async def auto_save_session_to_memory(session, memory_service):
    """R5 compliance callback."""
    if session and memory_service:
        await memory_service.save_session(
            session_id=session.id,
            session_data=session.to_dict(),
            metadata={
                "timestamp": session.updated_at,
                "agent": "agent-name",
                "compliance": "R5"
            }
        )
```

### Pattern 4: Workflow Coordination

```python
class WorkflowConfig(BaseModel):
    pattern: str  # "sequential", "parallel", "loop"
    agents: List[str]
    max_iterations: int = 10

async def coordinate_workflow(
    workflow: WorkflowConfig,
    input_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Coordinates multi-agent workflows."""

    if workflow.pattern == "sequential":
        # Chain agents
        result = input_data
        for agent in workflow.agents:
            result = await invoke_agent(agent, result)

    elif workflow.pattern == "parallel":
        # Run concurrently
        tasks = [invoke_agent(agent, input_data)
                for agent in workflow.agents]
        results = await asyncio.gather(*tasks)

    elif workflow.pattern == "loop":
        # Iterate until condition
        for i in range(workflow.max_iterations):
            result = await invoke_agent(workflow.agents[0], input_data)
            if result.get("complete"):
                break

    return {"pattern": workflow.pattern, "results": results}
```

---

## Deployment Patterns

### Vertex AI Engine Deployment

```yaml
# deploy.yaml
apiVersion: agents.vertex.ai/v1
kind: AgentDeployment
metadata:
  name: agent-name
spec:
  agent:
    source: ./
    entrypoint: agent.root_agent
    runtime: python310
  resources:
    cpu: 4
    memory: 8Gi
  replicas:
    min: 2
    max: 10
  service:
    type: LoadBalancer
    port: 8080
```

### CI/CD Pipeline

```yaml
# .github/workflows/deploy.yml
name: Deploy to Vertex AI Engine
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: google-github-actions/auth@v2
      - name: Deploy Agent
        run: |
          adk deploy agent_engine \
            --project=${{ secrets.PROJECT_ID }} \
            --location=us-central1 \
            --config=agent/deploy.yaml
```

---

## Migration Strategy

### Phase 1: Core Structure (Week 1)
1. Create `agent/` directory
2. Implement `agent.py` with get_agent()
3. Create `tools.py` with FunctionTool
4. Add `agent_card.yaml`

### Phase 2: Memory & Session (Week 2)
1. Implement create_runner()
2. Configure VertexAiSessionService
3. Configure VertexAiMemoryBankService
4. Add auto_save callback

### Phase 3: A2A Protocol (Week 3)
1. Implement discovery endpoints
2. Add invocation handlers
3. Create agent registry
4. Test inter-agent communication

### Phase 4: Deployment (Week 4)
1. Create deploy.yaml
2. Set up CI/CD pipeline
3. Configure monitoring
4. Deploy to Vertex AI Engine

### Phase 5: Production Hardening (Week 5)
1. Add circuit breakers
2. Implement rate limiting
3. Set up alerts
4. Performance optimization

---

## Best Practices

### 1. Tool Design
- Use Pydantic models for inputs
- Return structured dictionaries
- Handle errors gracefully
- Include tool_context parameter

### 2. Memory Management
- Save sessions after each interaction
- Implement 14-day TTL for R5
- Index by agent, task, timestamp
- Enable semantic search

### 3. Error Handling
- Retry with exponential backoff
- Implement circuit breakers
- Log all failures
- Provide fallback options

### 4. Security
- Validate all inputs
- Use OAuth 2.0 for auth
- Encrypt sensitive data
- Audit all operations

### 5. Performance
- Enable parallel tool calls
- Cache agent cards
- Reuse sessions
- Monitor latency

---

## Compliance Requirements

### R5 Compliance
- Auto-save sessions to Memory Bank
- 14-day data retention
- Proper deletion procedures
- Audit trail maintenance

### SOC 2
- Security controls
- Availability monitoring
- Confidentiality measures
- Privacy protection

### GDPR
- Data minimization
- Right to deletion
- Consent management
- Data portability

---

## Testing Strategy

### Unit Tests
```python
# tests/test_agent.py
import pytest
from agent import get_agent, create_runner

def test_agent_creation():
    agent = get_agent()
    assert agent.name == "expected-name"
    assert len(agent.tools) > 0

@pytest.mark.asyncio
async def test_runner_creation():
    runner = await create_runner()
    assert runner.session_service is not None
    assert runner.memory_service is not None
```

### Integration Tests
- A2A protocol communication
- Memory Bank persistence
- Session management
- Tool execution

### Load Tests
- 1000 requests/minute
- Concurrent agent invocations
- Memory usage under load
- Latency distribution

---

## Monitoring & Observability

### Metrics to Track
- Agent invocation count
- Response time (p50, p95, p99)
- Error rate
- Memory usage
- Session count
- Tool execution time

### Dashboards
- Real-time agent status
- Workflow execution flow
- Error distribution
- Performance trends

### Alerts
- Agent unavailable > 1 minute
- Error rate > 1%
- Response time p99 > 10s
- Memory usage > 80%

---

## Example: Complete Plugin Transformation

### Before (Instruction-based)
```
plugins/ai-ml/jeremy-adk-orchestrator/
├── .claude-plugin/plugin.json
├── agents/adk-deployment-specialist.md
├── commands/deploy-to-vertex.md
└── skills/orchestrating-agents/SKILL.md
```

### After (ADK-compliant)
```
plugins/ai-ml/jeremy-adk-orchestrator/
├── .claude-plugin/plugin.json
├── agent/                        # NEW
│   ├── __init__.py
│   ├── agent.py                 # Executable Python agent
│   ├── tools.py                 # 8 FunctionTools
│   ├── system-prompt.md         # Instructions
│   ├── agent_card.yaml          # A2A discovery
│   ├── requirements.txt         # Dependencies
│   ├── deploy.yaml              # Vertex AI config
│   └── .env.example
├── agents/                       # Kept for Claude Code
├── commands/                     # Kept for Claude Code
├── skills/                       # Kept for Claude Code
├── tests/                        # NEW
├── terraform/                    # NEW
└── monitoring/                   # NEW
```

---

## Conclusion

This architecture enables jeremy-* plugins to evolve from instruction-based templates to production-ready ADK agents while maintaining backward compatibility with Claude Code. The dual approach (instructions + executable) provides maximum flexibility for both development and production deployment scenarios.

---

**Document Version**: 1.0.0
**Last Updated**: 2025-11-19
**Review Date**: 2025-12-19
**Classification**: Technical Architecture