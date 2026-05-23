# Workflow Examples

## Workflow Examples

### Example 1: GCP Deployment Agent

**User**: "Create an ADK agent that deploys GCP resources"

**Implementation**:

```python
from google.adk.agents import Agent
from google.adk.tools import FunctionTool

def deploy_gke_cluster(cluster_name: str, region: str, node_count: int = 3) -> str:
    """Deploy a GKE cluster with the given parameters."""
    # Implementation would call GCP APIs
    return f"GKE cluster '{cluster_name}' created in {region} with {node_count} nodes"

def deploy_cloud_run(service_name: str, image: str, region: str) -> str:
    """Deploy a Cloud Run service from a container image."""
    return f"Cloud Run service '{service_name}' deployed from {image} in {region}"

deployment_agent = Agent(
    name="gcp-deployer",
    model="gemini-2.5-flash",
    tools=[deploy_gke_cluster, deploy_cloud_run],
    instruction="""
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
    """,
)

# Deploy to Agent Engine via Python SDK
import vertexai

client = vertexai.Client(project="my-project", location="us-central1")
remote_agent = client.agent_engines.create(
    agent_engine=deployment_agent,
    requirements=["google-adk>=1.15.1"],
    display_name="gcp-deployer",
)
```

### Example 2: Multi-Agent Pipeline System

**User**: "Build a multi-agent pipeline with ADK orchestrating retrieval and analysis"

**Implementation**:

```python
from google.adk.agents import Agent, SequentialAgent

def retrieve_documents(query: str) -> str:
    """Retrieve relevant documents from Vertex AI Search."""
    # Implementation calls Vertex AI Search
    return f"Retrieved 5 documents matching: {query}"

def analyze_documents(documents: str) -> str:
    """Analyze retrieved documents and extract insights."""
    return f"Analysis complete: key themes identified from {documents}"

# Sub-Agent 1: Document Retriever
retriever_agent = Agent(
    name="retriever",
    model="gemini-2.5-flash",
    tools=[retrieve_documents],
    instruction="Retrieve relevant documents for the user's query.",
)

# Sub-Agent 2: Document Analyzer
analyzer_agent = Agent(
    name="analyzer",
    model="gemini-2.5-pro",  # More powerful model for analysis
    tools=[analyze_documents],
    instruction="Analyze retrieved documents and generate comprehensive insights.",
)

# Orchestrator runs them in sequence
orchestrator = SequentialAgent(
    name="rag-pipeline",
    sub_agents=[retriever_agent, analyzer_agent],
    description="First retrieve docs, then generate analysis",
)
```

### Example 3: Deploying and Managing Agents via SDK

**User**: "Deploy a GKE cluster agent and check its status"

**Implementation**:

```python
import vertexai

# Initialize client
client = vertexai.Client(project="my-project", location="us-central1")

# Deploy agent
remote_agent = client.agent_engines.create(
    agent_engine=deployment_agent,
    requirements=["google-adk>=1.15.1", "google-cloud-container>=2.0.0"],
    display_name="gke-deployer",
)
print(f"Deployed: {remote_agent.resource_name}")

# Query the deployed agent
response = remote_agent.query(
    input="Deploy GKE cluster named prod-api with 5 nodes in us-central1"
)
print(f"Response: {response}")

# List all deployed agents
for agent in client.agent_engines.list():
    print(f"  {agent.display_name}: {agent.resource_name}")

# Get a specific deployed agent
agent = client.agent_engines.get(
    name="projects/my-project/locations/us-central1/reasoningEngines/12345"
)
print(f"Agent status: {agent.display_name}")

# Delete an agent when no longer needed
# client.agent_engines.delete(name=agent.resource_name)
```

### Example 4: Agent with Session Persistence

**User**: "Build a stateful agent that remembers context across turns"

**Implementation**:

```python
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import VertexAiSessionService

agent = Agent(
    name="stateful-assistant",
    model="gemini-2.5-flash",
    instruction="You are a helpful assistant. Remember user preferences from prior turns.",
)

session_service = VertexAiSessionService(
    project="my-project",
    location="us-central1",
)

runner = Runner(
    app_name="stateful-app",
    agent=agent,
    session_service=session_service,
)

# Turn 1: User sets preference
# runner.run(user_id="user-1", session_id="sess-1", new_message=...)
# Turn 2: Agent remembers preference from Turn 1
# runner.run(user_id="user-1", session_id="sess-1", new_message=...)
```
