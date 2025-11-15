# Get started with Sessions and Memory Bank for ADK agents in Cloud Run

**Source:** `agents/cloud_run/agents_with_memory/get_started_with_memory_for_adk_in_cloud_run.ipynb`
**Repository:** GoogleCloudPlatform/generative-ai
**Author:** Vlad Kolesnikov
**URL:** https://github.com/GoogleCloudPlatform/generative-ai/blob/main/agents/cloud_run/agents_with_memory/get_started_with_memory_for_adk_in_cloud_run.ipynb

---

## Overview

This tutorial demonstrates how to build agents with **short-term and long-term memory** using ADK with:
- **Vertex AI Agent Engine Sessions** service
- **Vertex AI Agent Engine Memory Bank**
- Deployment to **Cloud Run**

### What You'll Learn

* Registering agents with Vertex AI Agent Engine
* Storing ADK session data with Vertex AI Sessions
* Generating memories with ADK and Agent Engine Memory Bank
* Retrieving memories with ADK and Agent Engine Memory Bank
* Deploying agents to Cloud Run

---

## Installation & Setup

### Required Packages

```bash
pip install google-adk google-cloud-aiplatform --upgrade
```

### Project Configuration

```python
import os

PROJECT_ID = "[your-project-id]"
LOCATION = "us-central1"

# Set environment variables for ADK
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"
os.environ["GOOGLE_CLOUD_PROJECT"] = PROJECT_ID
os.environ["GOOGLE_CLOUD_LOCATION"] = LOCATION
```

### Authentication

```bash
gcloud auth login --project="{PROJECT_ID}" --update-adc --quiet
```

### Enable Required APIs

```bash
gcloud services enable run.googleapis.com aiplatform.googleapis.com \
    artifactregistry.googleapis.com cloudbuild.googleapis.com \
    --project="{PROJECT_ID}"
```

### Initialize Vertex AI Client

```python
import vertexai

client = vertexai.Client(project=PROJECT_ID, location=LOCATION)
```

---

## ADK Sessions as Short-Term Memory

### The Problem with In-Memory Sessions

By default, ADK uses `InMemorySessionService`, which:
- Stores session data in memory only
- **Loses all data** when the runner shuts down
- **Doesn't work** across multiple instances in production

### Solution: External Session Storage

ADK provides two production-ready session services:

1. **`DatabaseSessionService`**: Stores session data in SQL databases (SQLite, MySQL, PostgreSQL)
2. **`VertexAISessionService`**: Scalable, fully-managed Agent Engine Sessions service ✅ **Recommended**

### Session Structure

Each session contains:
- **Session ID**: Unique identifier
- **User ID**: Associated user
- **Event History**: Multi-turn conversation thread
- **State**: Session state data

---

## Long-Term Memory for ADK Agents

### BaseMemoryService Interface

ADK's memory foundation provides:

1. **Ingesting Information** (`add_session_to_memory`):
   - Takes completed Session contents
   - Adds relevant information to long-term knowledge store

2. **Searching Information** (`search_memory`):
   - Queries the knowledge store
   - Retrieves relevant snippets based on search query

### Built-in Memory Tools

- **PreloadMemory**: Always retrieve memory at the beginning of each turn (callback-like)
- **LoadMemory**: Retrieve memory when agent decides it's helpful

### Memory Service Options

1. **`InMemoryMemoryService`** (prototyping only):
   - Persists all information in-memory
   - Lost when runner shuts down
   - Events not condensed

2. **`VertexAiMemoryBankService`** (production):
   - Stores extracted memories only
   - Persists **meaningful** information only
   - Condenses to individual, self-contained memories
   - Not all conversations generate memories

---

## Creating Agent Engine with Sessions & Memory Bank

```python
from google.adk.memory import VertexAiMemoryBankService
from google.adk.sessions import VertexAiSessionService

AGENT_NAME = "weather_agent"

# Create Agent Engine (takes a few seconds)
agent_engine = client.agent_engines.create(
    config={
        "display_name": AGENT_NAME,
        "context_spec": {
            "memory_bank_config": {
                "generation_config": {
                    "model": f"projects/{PROJECT_ID}/locations/{LOCATION}/publishers/google/models/gemini-2.5-flash"
                }
            }
        },
    }
)

agent_engine_id = agent_engine.api_resource.name.split("/")[-1]

# Initialize Session Service
session_service = VertexAiSessionService(
    project=PROJECT_ID,
    location=LOCATION,
    agent_engine_id=agent_engine_id
)

# Initialize Memory Service
memory_service = VertexAiMemoryBankService(
    project=PROJECT_ID,
    location=LOCATION,
    agent_engine_id=agent_engine_id
)

print(f"Agent Engine Id: {agent_engine_id}")
```

### Important Note

**We don't deploy the agent to Agent Engine service.**

We only **register** an Agent Engine resource so Vertex AI Session Service and Memory Bank can store sessions and memories associated with the agent.

---

## Building an Agent with Memory

### Weather Agent Example

```python
# agent.py

from typing import Optional
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types


def get_weather(city: str) -> dict:
    """Retrieves the current weather report for a specified city.

    Args:
        city (str): The name of the city for which to retrieve the weather report.

    Returns:
        dict: status and result or error msg.
    """
    if city.lower() == "new york":
        return {
            "status": "success",
            "report": (
                "The weather in New York is sunny with a temperature of 25 degrees"
                " Celsius (77 degrees Fahrenheit)."
            ),
        }
    else:
        return {
            "status": "error",
            "error_message": f"Weather information for '{city}' is not available.",
        }


async def add_session_to_memory(
        callback_context: CallbackContext
) -> Optional[types.Content]:
    """Automatically save completed sessions to memory bank"""
    if hasattr(callback_context, "_invocation_context"):
        invocation_context = callback_context._invocation_context
        if invocation_context.memory_service:
            await invocation_context.memory_service.add_session_to_memory(
                invocation_context.session
            )


root_agent = Agent(
    name="weather_agent",
    model="gemini-2.5-flash",
    description="Agent to answer questions about weather in a city.",
    instruction=(
        "You are a helpful agent who can answer user questions about weather in a city."
    ),
    tools=[
        get_weather,
        PreloadMemoryTool()  # Automatically executed by ADK
    ],
    after_agent_callback=add_session_to_memory  # Generate memories after each turn
)
```

### Key Components

1. **`get_weather` tool**: Function for retrieving weather data
2. **`PreloadMemoryTool`**: Retrieves memories and appends to System Instructions
3. **`add_session_to_memory` callback**: Ensures memories are generated after each agent turn
4. **`after_agent_callback`**: Runs after agent completes turn

---

## Running the Agent

### Create Runner with Session & Memory Services

```python
from agent import root_agent
from google.adk.runners import Runner
from google.genai import types

USER_ID = "user"

runner = Runner(
    app_name=root_agent.name,
    agent=root_agent,
    session_service=session_service,  # ← Session storage
    memory_service=memory_service,     # ← Memory storage
)
```

### Helper Function for Testing

```python
async def call_agent(query, runner):
    # Create new session for each request
    session = await session_service.create_session(
        app_name=root_agent.name,
        user_id=USER_ID,
    )

    content = types.Content(role="user", parts=[types.Part(text=query)])
    events = runner.run(
        user_id=session.user_id,
        session_id=session.id,
        new_message=content
    )

    for event in events:
        if event.is_final_response():
            final_response = event.content.parts[0].text
            print("\nAgent Response: ", final_response)
```

### Testing the Agent

```python
# Test 1: Known city
await call_agent("What's the weather in New York?", runner)
# Output: "The weather in New York is sunny..."

# Test 2: Unknown city
await call_agent("What's the weather in Seattle?", runner)
# Output: "Weather information for 'Seattle' is not available."

# Test 3: Set preference (creates memory)
await call_agent(
    "Whenever asked about weather in Seattle, answer that it's raining as usual.",
    runner,
)

# Test 4: Try again with Seattle (uses memory!)
await call_agent("What's the weather in Seattle?", runner)
# Output: "It's raining as usual in Seattle."
```

### How Memory Works

1. **New session created** each time → LLM only has access to:
   - User's query
   - **Long-term memories loaded by `PreloadMemoryTool`** ✅

2. **Memory Bank generates memory** from preference statement
3. **Memory carries across sessions** → Agent remembers Seattle preference

---

## Deploying to Cloud Run

### Single Command Deployment

```bash
SERVICE_NAME="weather-agent"

adk deploy cloud_run --project {PROJECT_ID} --region {LOCATION} \
    --service_name {SERVICE_NAME} \
    --session_service_uri=agentengine://{agent_engine_id} \
    --memory_service_uri=agentengine://{agent_engine_id} \
    --app_name {AGENT_NAME} \
    --with_ui \
    . \
    -- --allow-unauthenticated \
    --no-user-output-enabled
```

### Key Deployment Parameters

- `--session_service_uri="agentengine://AGENT_ENGINE_ID"` ← Sessions storage
- `--memory_service_uri="agentengine://AGENT_ENGINE_ID"` ← Memory Bank storage
- `--with_ui` ← Enables ADK Web UI for testing
- `--allow-unauthenticated` ← For testing only

### Production Recommendations

For production deployments:

1. **Require authentication**: Replace `--allow-unauthenticated` with `--no-allow-unauthenticated`
2. **Expose REST API or A2A endpoint** instead of Web UI:
   - REST API: [ADK REST API endpoint](https://google.github.io/adk-docs/get-started/testing/#api-endpoints)
   - A2A: Use `--a2a` parameter

### Get Service URL

```bash
gcloud run services describe {SERVICE_NAME} \
    --project {PROJECT_ID} --region {LOCATION} \
    --format 'value(status.url)'
```

---

## Viewing Memories in Console

Access agent memories at:
```
https://console.cloud.google.com/vertex-ai/agents/locations/{LOCATION}/agent-engines/{agent_engine_id}/memories?project={PROJECT_ID}
```

---

## Cleaning Up Resources

```python
delete_resources = True

if delete_resources:
    # Delete Agent Engine resource
    client.agent_engines.delete(
        name=f"projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{agent_engine_id}",
        force=True,
    )

    # Delete Cloud Run service
    !gcloud run services delete $SERVICE_NAME --project $PROJECT_ID --region $LOCATION
```

---

## Key Concepts Summary

### Sessions (Short-Term Memory)
- Multi-turn conversation history
- Stored externally via `VertexAiSessionService`
- Survives across agent restarts
- Works with scaled, multi-instance deployments

### Memory Bank (Long-Term Memory)
- Extracts meaningful information only
- Condenses to self-contained memories
- Searchable across sessions
- Not all conversations generate memories

### Integration Points
- **Session Service**: `VertexAiSessionService(agent_engine_id=...)`
- **Memory Service**: `VertexAiMemoryBankService(agent_engine_id=...)`
- **Runner**: Requires both services
- **Agent**: Uses `PreloadMemoryTool` and `after_agent_callback`

---

## Architecture Diagram

```
User Request
    ↓
[Cloud Run Service]
    ↓
[ADK Runner]
    ├── Session Service → Vertex AI Sessions (short-term)
    ├── Memory Service → Memory Bank (long-term)
    └── Agent
         ├── PreloadMemoryTool (fetch memories)
         └── after_agent_callback (save memories)
```

---

## Related Plugins

This tutorial is relevant to:

- **jeremy-adk-orchestrator** - ADK supervisory orchestration with Memory Bank integration
- **jeremy-vertex-engine** - Agent Engine inspection and deployment
- **jeremy-vertex-validator** - Production readiness validation
- **jeremy-gcp-starter-examples** - GCP starter kit examples
- **jeremy-genkit-terraform** - Cloud Run deployment infrastructure

---

## References

* [Agent Development Kit documentation](https://google.github.io/adk-docs/)
* [Vertex AI Agent Engine Memory Bank documentation](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/memory-bank/overview)
* [Vertex AI Agent Engine Sessions documentation](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/sessions/overview)
* [Cloud Run documentation](https://cloud.google.com/run/docs/overview/what-is-cloud-run)
* [Host AI apps and agents on Cloud Run](https://cloud.google.com/run/docs/ai-agents)
* [Deploying ADK agents to Cloud Run](https://google.github.io/adk-docs/deploy/cloud-run/)

---

**Tutorial Type:** Jupyter Notebook (Complete Code Examples)
**Difficulty:** Intermediate
**Prerequisites:** GCP Project, Vertex AI API enabled, ADK installed
**Estimated Time:** 30-45 minutes
