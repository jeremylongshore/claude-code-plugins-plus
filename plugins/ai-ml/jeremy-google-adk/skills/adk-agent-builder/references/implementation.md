# ADK Agent Builder — Implementation Guide

## How the Skill Works

1. **Scope confirmation**: Determines if user wants local-only scaffold or full Vertex AI deployment
2. **Architecture selection**: Chooses ReAct (single agent) or orchestrated (multi-agent) based on task complexity
3. **Tool surface definition**: Identifies which tools the agent needs, maps to ADK Tool interface
4. **Scaffold generation**: Creates project structure with all required files
5. **Validation**: Runs smoke test to verify agent works before handing off

## ADK Project Structure

```
project-root/
├── src/
│   ├── agents/
│   │   ├── __init__.py
│   │   └── main_agent.py       # Agent entrypoint with system prompt + tools
│   └── tools/
│       ├── __init__.py
│       └── custom_tool.py      # Each tool in its own file
├── tests/
│   ├── test_tools.py           # Unit tests for tool functions
│   └── test_agent.py           # Smoke prompt tests for agent behavior
├── pyproject.toml              # Dependencies: google-adk, tool-specific packages
├── .env.example                # Required environment variables (never actual values)
└── README.md                   # Setup and usage instructions
```

## Tool Registry Pattern

Every tool follows the ADK `@Tool` decorator pattern:

```python
from google.adk.tools import Tool

@Tool(description="Clear description of what this tool does and when to use it")
def tool_name(param1: str, param2: int = 10) -> str:
    """Typed parameters. Return string for agent consumption."""
    result = do_something(param1, param2)
    return f"Result: {result}"
```

Tools are registered in the Agent constructor:
```python
agent = Agent(
    name="agent-name",
    model="gemini-2.0-flash",
    system_prompt="...",
    tools=[tool_a, tool_b, tool_c],
)
```

**Adding a new tool**: Create file in `src/tools/`, import in agent file, add to `tools=[]` list.

## Multi-Agent Orchestration

ADK provides three built-in orchestration patterns:

| Pattern | Use Case | How It Works |
|---------|----------|-------------|
| `SequentialAgent` | Pipeline workflows | Agent A → Agent B → Agent C (output chains) |
| `ParallelAgent` | Independent subtasks | Agents A, B, C run simultaneously, results merged |
| `LoopAgent` | Iterative refinement | Agent runs repeatedly until exit condition met |

Custom orchestrators combine these:
```python
pipeline = SequentialAgent(
    name="research-pipeline",
    agents=[
        ParallelAgent(name="gather", agents=[web_researcher, doc_scanner]),
        synthesizer,
        LoopAgent(name="refine", agent=quality_checker, max_iterations=3),
    ],
)
```

## Testing Strategy

**Unit tests**: Test each tool function in isolation with mocked external APIs.

```python
def test_fetch_pr_diff(mock_github):
    mock_github.return_value = {"files": [{"filename": "app.py", "changes": 5}]}
    result = fetch_pr_diff("owner/repo", 42)
    assert "app.py" in result
```

**Smoke prompts**: Run the full agent against a known scenario.

```python
def test_agent_smoke():
    response = agent.run("Summarize the changes in PR #42")
    assert len(response) > 100  # Non-trivial response
    assert "changes" in response.lower()
```

## Deployment Pipeline

```
Local Development        Staging                  Production
────────────────────     ─────────────────        ──────────────────
adk run --local          adk deploy --staging     adk deploy --prod
pytest tests/            curl health-check        gcloud monitoring
manual smoke test        automated eval suite     alerting + logging
```

**Local**: `adk run --prompt "test prompt"` — runs agent in local Python process.

**Staging**: Deploy to Agent Engine with `--staging` flag, run automated test suite.

**Production**: Deploy with monitoring, set up Cloud Monitoring alerts for error rate and latency.

## Configuration Reference

**Environment Variables**:
| Variable | Required | Purpose |
|----------|----------|---------|
| `GOOGLE_CLOUD_PROJECT` | For deployment | GCP project ID |
| `GOOGLE_CLOUD_REGION` | For deployment | Default: `us-central1` |
| `GOOGLE_APPLICATION_CREDENTIALS` | For local dev | Path to service account key |

**pyproject.toml**:
```toml
[project]
name = "my-agent"
requires-python = ">=3.10"
dependencies = [
    "google-adk>=0.3.0",
    # Add tool-specific dependencies here
]

[project.optional-dependencies]
dev = ["pytest", "pytest-asyncio"]
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
