# Examples

## Natural Language Prompts

These prompts activate the skill and demonstrate common usage patterns:

### Deployment

- "Deploy this ADK agent to Agent Engine with session persistence enabled."
- "Create a reasoning engine from my agent.py with gemini-2.5-flash."
- "Deploy my multi-agent pipeline to Vertex AI Agent Engine in us-central1."

### Agent Management (SDK)

- "List all deployed agents in my project using the Vertex AI SDK."
- "Get the status of reasoning engine ID 12345 in us-central1."
- "Delete the old version of my sentiment-analysis agent from Agent Engine."

### Multi-Agent Orchestration

- "Build a SequentialAgent pipeline: validate config, deploy resources, run health check."
- "Create a ParallelAgent that runs data extraction and sentiment analysis simultaneously."
- "Set up a LoopAgent that retries deployment until health check passes (max 5 iterations)."

### A2A Protocol

- "Expose an A2A AgentCard at `/.well-known/agent-card` for my deployed agent."
- "Send a task to the agent at [endpoint] using A2A JSON-RPC protocol."
- "Discover capabilities of the agent at [endpoint] via its AgentCard."

### Session & Memory

- "Create a stateful agent with VertexAiSessionService for cross-turn persistence."
- "Set up a runner with session auto-save for compliance."
- "Query my deployed agent with session_id to maintain conversation context."

## Code Snippets

### Deploy an Agent

```python
import vertexai
from google.adk.agents import Agent

agent = Agent(
    name="my-agent",
    model="gemini-2.5-flash",
    instruction="You help users analyze data.",
    tools=[my_analysis_tool],
)

client = vertexai.Client(project="my-project", location="us-central1")
remote = client.agent_engines.create(
    agent_engine=agent,
    requirements=["google-adk>=1.15.1"],
    display_name="data-analyst",
)
print(f"Deployed: {remote.resource_name}")
```

### List and Query Agents

```python
import vertexai

client = vertexai.Client(project="my-project", location="us-central1")

# List all agents
for agent in client.agent_engines.list():
    print(f"{agent.display_name}: {agent.resource_name}")

# Get and query a specific agent
agent = client.agent_engines.get(
    name="projects/my-project/locations/us-central1/reasoningEngines/12345"
)
response = agent.query(input="Summarize Q3 revenue trends")
print(response)
```

### Multi-Agent Sequential Pipeline

```python
from google.adk.agents import Agent, SequentialAgent

extractor = Agent(name="extractor", model="gemini-2.5-flash", instruction="Extract key data points.")
analyzer = Agent(name="analyzer", model="gemini-2.5-pro", instruction="Analyze extracted data.")
reporter = Agent(name="reporter", model="gemini-2.5-flash", instruction="Generate summary report.")

pipeline = SequentialAgent(
    name="etl-pipeline",
    sub_agents=[extractor, analyzer, reporter],
    description="Extract -> Analyze -> Report",
)
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
