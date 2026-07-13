# ADK Engineer — Implementation Guide

## How the Skill Works

1. **Requirement analysis**: Parse the user request to identify agent goals, required tools, orchestration pattern (single/sequential/parallel/loop), and deployment target (local or Agent Engine)
2. **Project discovery**: Glob and Read existing files to understand the current codebase — runtime language, existing agents/tools, test framework, and dependency versions
3. **Architecture proposal**: Generate a module layout with clear boundaries: agent entrypoints, tool modules, shared config, and test directories
4. **Incremental implementation**: Write or patch one tool at a time, each with input validation, structured return format (`{status, data/error}`), and a corresponding test
5. **Validation and delivery**: Run the test suite via Bash, verify all pass, and produce a summary with deployment instructions when applicable

## Project/File Structure

```
adk-project/
├── src/
│   ├── __init__.py
│   ├── agent.py              # Agent definition(s) + system instruction
│   ├── tools.py              # FunctionTool wrappers
│   ├── config.py             # AgentConfig dataclass
│   └── orchestrator.py       # Multi-agent pipeline (if applicable)
├── tests/
│   ├── __init__.py
│   ├── test_agent.py         # Agent creation and config tests
│   ├── test_tools.py         # Tool function unit tests
│   ├── conftest.py           # Shared fixtures and mocks
│   └── test_orchestrator.py  # Pipeline integration tests
├── pyproject.toml
├── requirements.txt
└── deploy/
    ├── deploy.sh             # Agent Engine deployment script
    └── validate.sh           # Post-deploy health check
```

## Core Patterns

### Structured Tool Returns

Every tool function returns a consistent dict for predictable agent behavior:

```python
def my_tool(input_param: str) -> dict:
    """Tool description for the LLM."""
    try:
        result = do_work(input_param)
        return {"status": "success", "data": result}
    except SpecificError as e:
        return {"status": "error", "error": str(e)}
```

### Dependency Injection for Testing

Use Python Protocol classes to decouple agent logic from live LLM calls:

```python
from typing import Protocol, Optional

class LLMProvider(Protocol):
    def run(self, message: str, session_id: Optional[str] = None) -> object: ...

def process(message: str, agent: Optional[LLMProvider] = None) -> str:
    if agent is None:
        agent = create_default_agent()
    response = agent.run(message)
    return response.text
```

### Multi-Agent Orchestration

```python
from google.adk.agents import Agent, SequentialAgent

pipeline = SequentialAgent(
    name="deploy-pipeline",
    sub_agents=[validator_agent, deployer_agent, monitor_agent],
)
result = pipeline.run("Deploy the service with config X")
```

## Configuration Reference

| Setting | Required | Default | Purpose |
|---------|----------|---------|---------|
| `GOOGLE_CLOUD_PROJECT` | Yes | — | Target GCP project for deployment |
| `GOOGLE_CLOUD_REGION` | No | `us-central1` | Region for Agent Engine deployment |
| `model` (in AgentConfig) | No | `gemini-2.5-flash` | LLM model for agent reasoning |
| `max_retries` (in AgentConfig) | No | `3` | Retry count for transient tool failures |
| `timeout_seconds` (in AgentConfig) | No | `30` | Per-tool execution timeout |
| `GOOGLE_APPLICATION_CREDENTIALS` | No | ADC | Service account key path (prefer WIF/ADC instead) |

## Testing Strategy

Run the full test suite before any commit or deployment:

```bash
# Unit tests with coverage
pytest tests/ -v --cov=src --cov-report=term-missing --tb=short

# Smoke test: verify agent creates without error
python -c "from src.agent import create_review_agent; a = create_review_agent(); print(f'{a.name}: {len(a.tools)} tools')"

# Integration test (requires ADK and model access)
python -m src.agent
```

Pass criteria:

- All unit tests pass (exit code 0)
- Coverage >= 80% on `src/` modules
- No import errors in smoke test
- Integration test produces structured output (for manual review)

## Deployment Pipeline

```bash
# 1. Local validation
pytest tests/ -v && echo "Tests pass"

# 2. Package for Agent Engine
pip freeze > requirements.txt
# Ensure only production deps (exclude pytest, dev tools)

# 3. Deploy to Agent Engine
python deploy/deploy.sh  # Wraps vertexai.Client().agent_engines.create()

# 4. Post-deploy validation
curl -s https://AGENT_ENDPOINT/.well-known/agent-card | jq .name
# Expect: agent name in response

# 5. Health check
python deploy/validate.sh  # Sends test prompt, checks response format
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
