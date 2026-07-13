# How It Works

## How It Works

### Phase 1: Agent Architecture Design

```
User Request -> Analyze:
- Single agent vs multi-agent system?
- Tools needed (Code Exec, Memory Bank, custom tools)?
- Orchestration pattern (Sequential, Parallel, Loop)?
- Integration with LangChain/Genkit?
- Deployment target (local, Agent Engine, Cloud Run)?
```

### Phase 2: ADK Agent Implementation

**Simple Agent (Python)**:

```python
from google.adk.agents import Agent

# Define agent with tools
agent = Agent(
    model="gemini-2.5-flash",
    name="gcp-deployer",
    description="GCP deployment specialist",
    instruction="""
You are a GCP deployment specialist.
Help users deploy resources securely.
    """,
    tools=[my_deploy_tool, my_validate_tool],
)
```

**Multi-Agent Orchestrator (Python)**:

```python
from google.adk.agents import Agent, SequentialAgent

# Define specialized sub-agents
validator_agent = Agent(
    name="validator",
    model="gemini-2.5-flash",
    instruction="Validate GCP configurations",
)

deployer_agent = Agent(
    name="deployer",
    model="gemini-2.5-flash",
    instruction="Deploy validated GCP resources",
    tools=[deploy_tool],
)

monitor_agent = Agent(
    name="monitor",
    model="gemini-2.5-flash",
    instruction="Monitor deployment status",
)

# Orchestrate with Sequential pattern
orchestrator = SequentialAgent(
    name="deploy-orchestrator",
    sub_agents=[validator_agent, deployer_agent, monitor_agent],
    description="Coordinate validation -> deployment -> monitoring",
)
```

### Phase 3: Code Execution Integration

The Code Execution tool provides:

- **Security**: Isolated sandbox environment, no access to your system
- **State Persistence**: Stateful within a session
- **Stateful Sessions**: Builds on previous executions

```python
from google.adk.agents import Agent
from google.adk.tools import built_in_code_execution

# Agent with Code Execution
agent = Agent(
    name="code-runner",
    model="gemini-2.5-flash",
    tools=[built_in_code_execution],
    instruction="""
Execute code in the secure sandbox.
Remember previous operations in this session.
    """,
)
```

### Phase 4: Session & Memory Integration

Persistent conversation state across interactions:

```python
from google.adk.agents import Agent
from google.adk.sessions import VertexAiSessionService
from google.adk.runners import Runner

agent = Agent(
    name="stateful-agent",
    model="gemini-2.5-flash",
    instruction="Remember user preferences and project context",
)

# Session service persists state across turns
session_service = VertexAiSessionService(
    project="my-project",
    location="us-central1",
)

runner = Runner(
    app_name="my-app",
    agent=agent,
    session_service=session_service,
)

# Session 1 (Monday) — state persists via session_id
# runner.run(user_id="user-123", session_id="sess-abc", ...)
# Session 2 (Wednesday) — same session_id, agent remembers context
```

### Phase 5: Deploy to Agent Engine

Deploy agent to Vertex AI Agent Engine using the Python SDK:

```python
import vertexai

# Initialize the Vertex AI client
client = vertexai.Client(project="my-project", location="us-central1")

# Deploy agent to Agent Engine (creates a Reasoning Engine resource)
remote_agent = client.agent_engines.create(
    agent_engine=agent,
    requirements=["google-adk>=1.15.1", "google-cloud-aiplatform>=1.120.0"],
    display_name="gcp-deployer-agent",
)

print(f"Agent deployed: {remote_agent.resource_name}")
# projects/my-project/locations/us-central1/reasoningEngines/12345
```

After deployment, the agent is accessible via the Vertex AI API. There is no separate A2A HTTP endpoint automatically exposed -- you interact with the deployed agent through the SDK:

```python
# Query the deployed agent
response = remote_agent.query(input="Deploy a GKE cluster named prod-api")
print(response)

# List all deployed agents
agents = client.agent_engines.list()
for a in agents:
    print(f"{a.display_name}: {a.resource_name}")

# Get a specific agent by resource name
agent = client.agent_engines.get(
    name="projects/my-project/locations/us-central1/reasoningEngines/12345"
)
```

### Phase 6: A2A Protocol for Inter-Agent Communication

The A2A (Agent-to-Agent) protocol enables standardized communication between agents. When deploying with A2A support, agents expose an AgentCard at `/.well-known/agent-card`:

```python
import requests

def discover_agent(agent_url: str) -> dict:
    """Discover agent capabilities via A2A AgentCard."""
    response = requests.get(f"{agent_url}/.well-known/agent-card")
    card = response.json()
    print(f"Agent: {card['name']}")
    print(f"Skills: {[s['id'] for s in card.get('skills', [])]}")
    return card

def send_task(agent_url: str, message: str, token: str) -> dict:
    """Send a task via A2A protocol."""
    response = requests.post(
        f"{agent_url}/tasks/send",
        json={
            "jsonrpc": "2.0",
            "method": "tasks/send",
            "params": {
                "message": {"role": "user", "parts": [{"text": message}]}
            },
            "id": "req-1"
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    return response.json()
```
