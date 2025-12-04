---
name: create-adk-agent
description: Generate a production-ready AI agent using Google ADK with Claude integration
model: sonnet
---

# Create ADK Agent

I'll help you generate a production-ready AI agent using Google's Agent Development Kit (ADK) with Claude integration.

## Information Needed

Please provide the following details:

1. **Agent Name**: What should we call your agent? (e.g., "linkedin-intelligence-agent")

2. **Agent Purpose**: What will this agent do? (e.g., "Research and qualify sales leads from LinkedIn")

3. **Pattern Type**:
   - `react` - Single agent with reasoning + acting loop
   - `multi-agent` - Team of specialized agents
   - `workflow` - Deterministic multi-step process

4. **Tools Needed**: Which tools should the agent use?
   - LinkedIn scraper
   - Apollo enrichment
   - Clearbit lookup
   - Email finder
   - Web search
   - Custom tools

5. **LLM Model**: Which Claude model?
   - `claude-3-5-sonnet-20241022` (recommended for most tasks)
   - `claude-3-haiku-20240307` (fast and cheap)
   - `claude-3-5-opus-20241022` (most capable)

## Generated Output

Based on your requirements, I will create:

1. **Main Agent Implementation** (`agent.py`)
   - Complete agent class with Claude integration
   - Tool initialization and management
   - Error handling and retry logic
   - Observability (logging, metrics)

2. **Tool Implementations** (`tools/`)
   - Custom tool classes
   - Input/output schemas
   - Rate limiting and caching

3. **Configuration** (`config.yaml`)
   - Agent settings
   - API keys and credentials
   - Behavior parameters

4. **Tests** (`tests/`)
   - Unit tests for agent logic
   - Integration tests for tools
   - End-to-end workflow tests

5. **Deployment** (`Dockerfile`, `terraform/`)
   - Container configuration
   - Cloud Run deployment
   - Kubernetes manifests

6. **Documentation** (`README.md`)
   - Setup instructions
   - Usage examples
   - API reference

## Example Usage

```python
# Initialize your agent
agent = YourAgent()

# Run the agent
result = await agent.run({
    "input": "your-data",
    "goal": "your-objective"
})

# Results include:
# - Observations from each step
# - Actions taken
# - Final synthesized output
```

## Next Steps

After generation:
1. Install dependencies: `pip install -r requirements.txt`
2. Set environment variables in `.env`
3. Run tests: `pytest tests/`
4. Deploy: `docker build && gcloud run deploy`

Let me know your requirements and I'll generate the complete agent package!