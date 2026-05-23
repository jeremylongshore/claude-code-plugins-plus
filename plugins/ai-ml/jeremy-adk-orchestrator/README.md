# Jeremy ADK Orchestrator

**🎯 VERTEX AI AGENT ENGINE + ADK DEPLOYMENT ONLY**

Expert Agent-to-Agent (A2A) protocol manager for communicating with **Vertex AI Agent Development Kit (ADK)** agents deployed on **Agent Engine**.

## ⚠️ Important: What This Plugin Is For

**✅ THIS PLUGIN IS FOR:**

- **ADK agents** deployed to **Vertex AI Agent Engine** (fully-managed runtime)
- **A2A Protocol** communication between Claude Code and ADK agents
- **Multi-agent orchestration** with ADK supervisory agents
- **Python, Java, and Go ADK agents** on Agent Engine
- Agent Engine features: Code Execution Sandbox, Memory Bank, Sessions

**❌ THIS PLUGIN IS NOT FOR:**

- LangChain agents (use LangSmith)
- LlamaIndex agents (not ADK compatible)
- Cloud Run deployments (use `jeremy-genkit-terraform` with `--cloud-run`)
- Self-hosted agent infrastructure
- Non-ADK agent frameworks

## Overview

This plugin enables Claude Code to communicate with ADK agents deployed on Vertex AI Agent Engine using the standardized A2A (Agent-to-Agent) Protocol. It handles task submission, status checking, session management, and AgentCard discovery for building multi-agent systems.

**Key Capabilities:**

- AgentCard discovery and capability inspection
- Task submission with structured inputs
- Session management for Memory Bank persistence
- Status polling and result retrieval
- Streaming responses for long-running tasks
- Multi-agent orchestration with supervisory patterns

## Installation

```bash
/plugin install jeremy-adk-orchestrator@claude-code-plugins-plus
```

## Prerequisites & Dependencies

### Required Google Cloud Setup

**1. Google Cloud Project with APIs Enabled:**

```bash
# Enable required APIs
gcloud services enable aiplatform.googleapis.com \
    discoveryengine.googleapis.com \
    logging.googleapis.com \
    monitoring.googleapis.com \
    cloudtrace.googleapis.com \
    --project=YOUR_PROJECT_ID
```

**2. Authentication:**

```bash
# Application Default Credentials
gcloud auth application-default login

# Or use service account
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

**3. Required IAM Permissions:**

```yaml
# Minimum required roles:
- roles/aiplatform.user              # Query Agent Engine resources
- roles/discoveryengine.admin        # Manage agents and sessions
- roles/logging.viewer               # Read agent logs
- roles/monitoring.viewer            # Access metrics
```

### Required Python Packages

**Install via pip:**

```bash
# Core ADK SDK (required for agent development)
pip install google-adk>=1.15.1

# Vertex AI SDK with Agent Engine support
pip install google-cloud-aiplatform[agent_engines]>=1.120.0

# A2A Protocol SDK (for protocol-level communication)
pip install a2a-sdk>=0.3.4

# HTTP client for REST API calls
pip install requests>=2.31.0

# Observability & Monitoring
pip install google-cloud-logging>=3.10.0
pip install google-cloud-monitoring>=2.21.0
pip install google-cloud-trace>=1.13.0
```

**All dependencies at once:**

```bash
pip install --upgrade \
    'google-adk>=1.15.1' \
    'google-cloud-aiplatform[agent_engines]>=1.120.0' \
    'a2a-sdk>=0.3.4' \
    'requests>=2.31.0' \
    'google-cloud-logging>=3.10.0' \
    'google-cloud-monitoring>=2.21.0' \
    'google-cloud-trace>=1.13.0'
```

### Agent Engine Management (Python SDK Only)

**There is no `gcloud` CLI for Agent Engine.** All management is done via the Python SDK:

```python
import vertexai

client = vertexai.Client(project="YOUR_PROJECT_ID", location="us-central1")

# List all deployed agents (reasoning engines)
for agent in client.agent_engines.list():
    print(f"{agent.display_name}: {agent.resource_name}")

# Get a specific agent
agent = client.agent_engines.get(
    name="projects/YOUR_PROJECT/locations/us-central1/reasoningEngines/12345"
)

# Delete an agent
# client.agent_engines.delete(name=agent.resource_name)
```

**Verify SDK Installation:**

```bash
python3 -c "import vertexai; print('Vertex AI SDK ready')"
python3 -c "import google.adk; print(f'ADK SDK version: {google.adk.__version__}')"
```

### ADK Agent Deployment Methods

**This plugin works with ADK agents deployed via:**

1. **ADK CLI Deployment:**

```bash
# Install ADK CLI
pip install google-adk

# Deploy agent to Agent Engine (interactive — prompts for project/location)
adk deploy cloud_run  # Deploy to Cloud Run
# Or deploy via the Python SDK (see method 2 below) for Agent Engine
```

1. **Python SDK Deployment:**

```python
from google.adk.agents import Agent
import vertexai

# Define ADK agent
agent = Agent(
    name="my-adk-agent",
    model="gemini-2.5-flash",
    instruction="Production ADK agent for deployment tasks.",
    tools=[my_tool_function],
)

# Deploy to Agent Engine
client = vertexai.Client(project=PROJECT_ID, location=LOCATION)
remote_agent = client.agent_engines.create(
    agent_engine=agent,
    requirements=["google-adk>=1.15.1"],
    display_name="my-adk-agent",
)

print(f"Agent deployed: {remote_agent.resource_name}")
```

1. **Terraform Deployment:**

```hcl
resource "google_vertex_ai_reasoning_engine" "adk_agent" {
  display_name = "my-adk-agent"
  region       = "us-central1"

  spec {
    agent_framework = "google-adk"  # ← Must specify ADK

    package_spec {
      pickle_object_gcs_uri    = "gs://bucket/agent.pkl"
      python_version           = "3.12"
      requirements_gcs_uri     = "gs://bucket/requirements.txt"
    }

    # Agent Engine features
    runtime_config {
      code_execution_config {
        enabled = true
      }
      memory_bank_config {
        enabled = true
      }
    }
  }
}
```

### ❌ NOT Compatible With

- **LangChain agents** (different framework, not ADK)
- **LlamaIndex agents** (not ADK compatible)
- **Cloud Run deployments** (use `jeremy-genkit-terraform`)
- **Cloud Functions** (not Agent Engine)
- **Self-hosted agent infrastructure** (requires Agent Engine runtime)
- **Non-Google agent frameworks** (Autogen, CrewAI, etc.)

## Features

✅ **AgentCard Discovery**: Automatic capability detection for ADK agents
✅ **A2A Protocol Communication**: Standardized task submission and retrieval
✅ **Session Management**: Persistent sessions with Memory Bank
✅ **Status Polling**: Real-time task status monitoring
✅ **Streaming Responses**: Handle long-running agent tasks
✅ **Multi-Agent Orchestration**: Supervisory agent patterns
✅ **Error Handling**: Retry logic and graceful degradation
✅ **Observability**: Integrated logging and tracing

## Components

### Agent

- **a2a-protocol-manager**: A2A protocol expert with task orchestration capabilities

### Skills (Auto-Activating)

- **a2a-protocol-manager**: Triggers on "communicate with ADK agent", "orchestrate agents", "send task to agent"
  - **Tool Permissions**: Read, Bash, Write, Grep (for agent communication)
  - **Version**: 1.0.0 (2026 schema compliant)

## Quick Start

### Natural Language Activation

Simply mention what you need:

```
"Communicate with the ADK agent at [endpoint]"
"Send a task to the sentiment-analysis agent"
"Orchestrate multiple ADK agents for this workflow"
"Check status of task ID abc-123"
"Discover capabilities of the agent at [endpoint]"
```

The skill auto-activates and handles A2A protocol communication.

## A2A Protocol Architecture

### Communication Flow

```
Claude Code Plugin
    ↓
AgentCard Discovery
    ↓ GET /.well-known/agent-card
Agent Metadata (capabilities, skills, schemas)
    ↓
Task Submission (A2A JSON-RPC 2.0)
    ↓ POST / (method: "tasks/send")
Task Created (task id, status)
    ↓
Task Status
    ↓ POST / (method: "tasks/get")
Task State (submitted, working, completed, failed)
    ↓
Result in task artifacts
    ↓ parts[].text / parts[].data
Agent Output
```

### AgentCard Discovery

**Discover agent capabilities before invocation:**

```python
import requests

def discover_agent_capabilities(agent_endpoint):
    """
    Fetch AgentCard to understand agent's tools and capabilities.

    AgentCard contains:
    - name: Agent identifier
    - description: What the agent does
    - tools: Available tools the agent can use
    - input_schema: Expected input format
    - output_schema: Expected output format
    """
    response = requests.get(f"{agent_endpoint}/.well-known/agent-card")
    agent_card = response.json()

    print(f"Agent: {agent_card['name']}")
    print(f"Description: {agent_card['description']}")
    print(f"Available tools: {[tool['name'] for tool in agent_card['tools']]}")

    return agent_card

# Example
agent_card = discover_agent_capabilities(
    "https://us-central1-aiplatform.googleapis.com/v1/projects/my-project/locations/us-central1/reasoningEngines/my-agent"
)
```

### Task Submission

**Submit a task to an ADK agent via A2A JSON-RPC:**

```python
import requests
import json

def submit_task(agent_endpoint, message_text, task_id=None):
    """
    Submit a task to an ADK agent via A2A protocol (JSON-RPC 2.0).

    Args:
        agent_endpoint: A2A-compliant agent URL
        message_text: Natural language instruction
        task_id: Optional task ID (generated if not provided)

    Returns:
        task_id: Unique identifier for tracking task status
    """
    import uuid
    task_id = task_id or str(uuid.uuid4())

    payload = {
        "jsonrpc": "2.0",
        "method": "tasks/send",
        "params": {
            "id": task_id,
            "message": {
                "role": "user",
                "parts": [{"text": message_text}],
            },
        },
        "id": f"req-{task_id}",
    }

    response = requests.post(
        agent_endpoint,
        json=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {get_access_token()}",
        }
    )

    result = response.json()
    task_status = result.get("result", {}).get("status", {}).get("state")

    print(f"Task submitted: {task_id}")
    print(f"Status: {task_status}")

    return task_id

# Example
task_id = submit_task(
    agent_endpoint="https://my-agent.example.com",
    message_text="Analyze sentiment of customer reviews",
)
```

### Status Polling

**Monitor task execution via A2A JSON-RPC:**

```python
import time

def poll_task_status(agent_endpoint, task_id, timeout=300):
    """
    Poll task status until completion or timeout.

    A2A task states:
    - submitted: Task queued
    - working: Agent is processing
    - input-required: Agent needs more info
    - completed: Task finished successfully
    - failed: Task encountered error
    - canceled: Task was canceled
    """
    start_time = time.time()

    while time.time() - start_time < timeout:
        payload = {
            "jsonrpc": "2.0",
            "method": "tasks/get",
            "params": {"id": task_id},
            "id": f"poll-{int(time.time())}",
        }

        response = requests.post(
            agent_endpoint,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {get_access_token()}",
            }
        )

        result = response.json().get("result", {})
        state = result.get("status", {}).get("state", "unknown")
        print(f"Status: {state}")

        if state == "completed":
            return result
        elif state == "failed":
            return result

        time.sleep(5)  # Poll every 5 seconds

    raise TimeoutError(f"Task {task_id} did not complete within {timeout}s")

# Example
result = poll_task_status(agent_endpoint, task_id)

state = result.get("status", {}).get("state")
if state == "completed":
    print("Task completed successfully!")
    artifacts = result.get("artifacts", [])
    for artifact in artifacts:
        for part in artifact.get("parts", []):
            print(f"Output: {part.get('text', '')}")
else:
    print(f"Task failed: {result.get('status', {}).get('message')}")
```

### Result Retrieval

**Get agent output (included in tasks/get response):**

In A2A, results are returned as `artifacts` in the `tasks/get` response -- there is no separate result endpoint. Each artifact contains `parts` (text, data, or file).

```python
def get_task_result(agent_endpoint, task_id):
    """
    Retrieve completed task output via tasks/get.

    Results are in the 'artifacts' field of the task response.
    Each artifact has 'parts' with text or structured data.
    """
    payload = {
        "jsonrpc": "2.0",
        "method": "tasks/get",
        "params": {"id": task_id},
        "id": f"result-{task_id}",
    }

    response = requests.post(
        agent_endpoint,
        json=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {get_access_token()}",
        }
    )

    task = response.json().get("result", {})
    artifacts = task.get("artifacts", [])

    print("Agent Output:")
    for artifact in artifacts:
        for part in artifact.get("parts", []):
            if "text" in part:
                print(part["text"])
            elif "data" in part:
                print(json.dumps(part["data"], indent=2))

    return artifacts

# Example
artifacts = get_task_result(agent_endpoint, task_id)
```

## Multi-Agent Orchestration

### Supervisory Agent Pattern

**Orchestrate multiple ADK agents:**

```python
class SupervisoryOrchestrator:
    """
    Coordinate multiple ADK agents for complex workflows.

    Pattern: Supervisor delegates tasks to specialized agents.
    """

    def __init__(self, agents_config):
        self.agents = {
            name: agent_config
            for name, agent_config in agents_config.items()
        }

    def orchestrate(self, workflow_input):
        """
        Execute multi-step workflow across agents.
        """
        results = {}
        session_id = None  # Shared session for Memory Bank

        # Step 1: Data extraction agent
        task_id, session_id = submit_task(
            self.agents['extractor']['endpoint'],
            {"input": workflow_input},
            session_id=session_id
        )
        status = poll_task_status(self.agents['extractor']['endpoint'], task_id)
        results['extracted_data'] = get_task_result(
            self.agents['extractor']['endpoint'],
            task_id
        )

        # Step 2: Analysis agent (uses extracted data)
        task_id, session_id = submit_task(
            self.agents['analyzer']['endpoint'],
            {"data": results['extracted_data']},
            session_id=session_id  # Continue same session
        )
        status = poll_task_status(self.agents['analyzer']['endpoint'], task_id)
        results['analysis'] = get_task_result(
            self.agents['analyzer']['endpoint'],
            task_id
        )

        # Step 3: Synthesis agent (combines results)
        task_id, session_id = submit_task(
            self.agents['synthesizer']['endpoint'],
            {
                "extracted": results['extracted_data'],
                "analyzed": results['analysis']
            },
            session_id=session_id
        )
        status = poll_task_status(self.agents['synthesizer']['endpoint'], task_id)
        results['final_output'] = get_task_result(
            self.agents['synthesizer']['endpoint'],
            task_id
        )

        return results

# Usage
orchestrator = SupervisoryOrchestrator({
    'extractor': {'endpoint': 'https://...'},
    'analyzer': {'endpoint': 'https://...'},
    'synthesizer': {'endpoint': 'https://...'}
})

workflow_results = orchestrator.orchestrate({
    "document": "Customer feedback report...",
    "analysis_type": "sentiment_and_topics"
})
```

## Observability & Monitoring

### Cloud Trace Integration

**Enable distributed tracing for A2A calls:**

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter

# Configure Cloud Trace
trace.set_tracer_provider(TracerProvider())
cloud_trace_exporter = CloudTraceSpanExporter()
tracer = trace.get_tracer(__name__)

# Instrument A2A protocol calls
with tracer.start_as_current_span("a2a_task_submission") as span:
    span.set_attribute("agent.endpoint", agent_endpoint)
    span.set_attribute("task.type", "sentiment_analysis")

    task_id, session_id = submit_task(agent_endpoint, task_input)

    span.set_attribute("task.id", task_id)
    span.set_attribute("session.id", session_id)

with tracer.start_as_current_span("a2a_task_polling") as span:
    status = poll_task_status(agent_endpoint, task_id)

    span.set_attribute("task.status", status['state'])
    span.set_attribute("task.latency_ms", status.get('latency'))
```

### Cloud Logging

**Query orchestration logs:**

```bash
# View all A2A protocol calls
gcloud logging read "jsonPayload.component=a2a_protocol AND resource.type=aiplatform.googleapis.com/Agent" \
    --project=YOUR_PROJECT_ID \
    --limit=100 \
    --format=json

# Filter by agent endpoint
gcloud logging read "jsonPayload.agent_endpoint=~'my-agent' AND severity>=WARNING" \
    --project=YOUR_PROJECT_ID \
    --limit=50
```

### Custom Metrics

**Track orchestration performance:**

```python
from google.cloud import monitoring_v3

def record_orchestration_metrics(
    task_id: str,
    latency_ms: float,
    success: bool
):
    """Record custom metrics for A2A orchestration."""
    client = monitoring_v3.MetricServiceClient()
    project_name = f"projects/{PROJECT_ID}"

    # Record task latency
    series = monitoring_v3.TimeSeries()
    series.metric.type = "custom.googleapis.com/adk/orchestration/latency"
    series.metric.labels['task_id'] = task_id

    point = monitoring_v3.Point()
    point.value.double_value = latency_ms
    point.interval.end_time.seconds = int(time.time())
    series.points = [point]

    client.create_time_series(name=project_name, time_series=[series])

    # Record success/failure
    series = monitoring_v3.TimeSeries()
    series.metric.type = "custom.googleapis.com/adk/orchestration/success_rate"

    point = monitoring_v3.Point()
    point.value.int64_value = 1 if success else 0
    point.interval.end_time.seconds = int(time.time())
    series.points = [point]

    client.create_time_series(name=project_name, time_series=[series])
```

## Storage Integration

### BigQuery Export

**Export orchestration logs to BigQuery:**

```python
from google.cloud import bigquery

def export_orchestration_history():
    """Export A2A protocol calls to BigQuery for analysis."""
    client = bigquery.Client(project=PROJECT_ID)

    # Create table for orchestration logs
    schema = [
        bigquery.SchemaField("timestamp", "TIMESTAMP"),
        bigquery.SchemaField("task_id", "STRING"),
        bigquery.SchemaField("session_id", "STRING"),
        bigquery.SchemaField("agent_endpoint", "STRING"),
        bigquery.SchemaField("status", "STRING"),
        bigquery.SchemaField("latency_ms", "FLOAT"),
        bigquery.SchemaField("input_tokens", "INTEGER"),
        bigquery.SchemaField("output_tokens", "INTEGER"),
        bigquery.SchemaField("error_message", "STRING"),
    ]

    table_ref = client.dataset("agent_analytics").table("orchestration_logs")
    table = bigquery.Table(table_ref, schema=schema)
    table = client.create_table(table, exists_ok=True)

    print(f"Created table: {table.project}.{table.dataset_id}.{table.table_id}")
```

**Query orchestration patterns:**

```sql
-- Most commonly orchestrated agents
SELECT
  agent_endpoint,
  COUNT(*) as total_calls,
  AVG(latency_ms) as avg_latency,
  SUM(CASE WHEN status = 'COMPLETED' THEN 1 ELSE 0 END) / COUNT(*) as success_rate
FROM `project.agent_analytics.orchestration_logs`
WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
GROUP BY agent_endpoint
ORDER BY total_calls DESC;

-- Multi-agent workflow analysis
SELECT
  session_id,
  COUNT(DISTINCT agent_endpoint) as num_agents,
  SUM(latency_ms) as total_latency,
  ARRAY_AGG(agent_endpoint ORDER BY timestamp) as agent_sequence
FROM `project.agent_analytics.orchestration_logs`
WHERE session_id IS NOT NULL
  AND timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
GROUP BY session_id
HAVING num_agents > 1
ORDER BY total_latency DESC;
```

## Use Cases

### Single Agent Communication

```
"Communicate with the sentiment-analysis ADK agent at [endpoint]"
"Send customer reviews to the analysis agent"
```

### Multi-Agent Workflows

```
"Orchestrate data extraction, analysis, and synthesis agents"
"Run a multi-step workflow across these ADK agents: [list]"
```

### Session Management

```
"Continue the conversation with session ID abc-123"
"Create a new session with Memory Bank persistence"
```

### Status Monitoring

```
"Check status of task ID xyz-456"
"Monitor the long-running analysis task"
```

### Capability Discovery

```
"Discover capabilities of the agent at [endpoint]"
"What tools does this ADK agent support?"
```

## Integration with Other Plugins

### jeremy-vertex-engine

- Orchestrator invokes agents → Inspector validates health
- A2A protocol calls → Performance monitoring

### jeremy-vertex-validator

- Validator checks agent code → Orchestrator deploys and tests
- Pre-deployment validation → Runtime orchestration

### jeremy-adk-terraform

- Terraform provisions agents → Orchestrator manages communication
- Infrastructure deployment → Runtime coordination

## Requirements

- Google Cloud Project with Vertex AI enabled
- ADK agents deployed on Agent Engine (NOT Cloud Run)
- Appropriate IAM permissions for A2A protocol
- Python 3.10+ (for ADK SDK compatibility)
- Cloud Logging enabled (for observability features)
- Cloud Monitoring enabled (for custom metrics)
- BigQuery dataset (for analytics integration - optional)

## License

MIT

## Support

- Issues: https://github.com/jeremylongshore/claude-code-plugins/issues
- Discussions: https://github.com/jeremylongshore/claude-code-plugins/discussions

## Version

2.1.0 (2026) - SDK accuracy fixes, expanded error/example references, corrected imports
