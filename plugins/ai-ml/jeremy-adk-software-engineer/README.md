# Jeremy ADK Software Engineer

Production-grade software engineering for Google Agent Development Kit (ADK) applications. Covers the full lifecycle: architecture design, agent implementation, testing, deployment automation, and multi-agent orchestration.

## Overview

This plugin provides an auto-activating skill that acts as a senior ADK software engineer. It helps you build maintainable, testable, and deployable ADK agents following Google Cloud best practices. Whether you are creating a single-agent tool-calling application or a multi-agent orchestration pipeline, this plugin delivers structured code, comprehensive tests, and deployment-ready configurations.

## Installation

```bash
/plugin install jeremy-adk-software-engineer@claude-code-plugins-plus
```

## Features

- **Agent Architecture Design**: Single-agent and multi-agent system patterns (Sequential, Parallel, Loop)
- **Clean Code Implementation**: Modular project structure with proper separation of concerns
- **Comprehensive Testing**: Unit, integration, and end-to-end test scaffolding with pytest
- **Deployment Automation**: CI/CD pipelines for Agent Engine, Cloud Run, and GKE
- **Tool Engineering**: Typed tool interfaces with FunctionTool, input validation, and structured outputs
- **Orchestration Patterns**: SequentialAgent, ParallelAgent, and custom workflow coordination
- **Production Guardrails**: Retries with backoff, timeouts, structured logging, and safe error messages
- **Multi-Language Support**: Python (primary), Java, and Go

## Components

| Type | Name | Description |
|------|------|-------------|
| Skill | `adk-engineer` (auto-activating) | Engineer production-ready ADK agents and multi-agent systems |

### Trigger Phrases

- "Build an ADK agent application"
- "Create production-ready ADK code"
- "Engineer a multi-agent system"
- "Implement ADK agent with tests"
- "Set up ADK development environment"
- "Design ADK agent architecture"

## Prerequisites

- Python 3.11+ (or Java/Go for alternative runtimes)
- `google-adk` package installed (`pip install google-adk`)
- Google Cloud project with Vertex AI API enabled
- `gcloud` CLI authenticated with appropriate IAM roles
- pytest for running tests (`pip install pytest pytest-cov`)

## Quick Start

```bash
pip install google-adk google-cloud-aiplatform[agent_engines]
```

Then ask Claude: "Build an ADK agent that [your use case]"

## Correct SDK Patterns

```python
# Agent import (correct)
from google.adk.agents import Agent
from google.adk.tools import FunctionTool

# Define a tool as a plain function
def get_weather(city: str) -> dict:
    """Fetch weather for a city."""
    return {"city": city, "temp_c": 22, "condition": "sunny"}

# Create agent with wrapped tools
root_agent = Agent(
    name="weather_agent",
    model="gemini-2.5-flash",
    description="Answers weather questions for any city.",
    instruction="Use the get_weather tool to answer user questions.",
    tools=[FunctionTool(func=get_weather)],
)
```

```bash
adk web  # Opens browser chat at http://localhost:8000
```

### Deployment

```python
# Deployment via SDK
import vertexai
client = vertexai.Client(project="PROJECT_ID", location="us-central1")
remote_agent = client.agent_engines.create(
    agent=app,
    config={
        "requirements": ["google-cloud-aiplatform[agent_engines,adk]"],
        "staging_bucket": "gs://BUCKET",
    },
)

# Deployment via CLI
# adk deploy agent_engine --project=PROJECT --region=REGION agent_module
```

> **Note:** There is no `gcloud` CLI for Agent Engine management. Use the Python SDK (`vertexai.Client().agent_engines.*`) or the `adk` CLI for deployment.

## Typical Project Structure

```
my-adk-project/
├── src/
│   ├── agents/              # Agent definitions
│   │   ├── __init__.py
│   │   └── main_agent.py
│   ├── tools/               # Custom tool functions
│   │   ├── __init__.py
│   │   └── custom_tools.py
│   ├── orchestrators/       # Multi-agent workflows
│   │   ├── __init__.py
│   │   └── workflows.py
│   └── config/
│       └── settings.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── deployment/              # Terraform / K8s configs
├── .github/workflows/       # CI/CD pipelines
├── requirements.txt
├── pyproject.toml
├── Dockerfile
└── README.md
```

## Use Cases

- **Greenfield Agent Development**: Scaffold a new ADK project from scratch with best practices
- **Production Hardening**: Add tests, error handling, and monitoring to an existing agent
- **Multi-Agent Systems**: Design and implement orchestrated agent teams
- **CI/CD Pipelines**: Generate GitHub Actions workflows for automated testing and deployment
- **Code Review Agents**: Build agents that lint, review, and analyze code quality

## Integration

Works with:

- [jeremy-gcp-starter-examples](../jeremy-gcp-starter-examples/) -- ADK sample code from google/adk-samples
- [jeremy-vertex-validator](../jeremy-vertex-validator/) -- Validate agents before deployment
- [jeremy-vertex-engine](../jeremy-vertex-engine/) -- Inspect deployed agents
- [jeremy-adk-orchestrator](../jeremy-adk-orchestrator/) -- A2A protocol orchestration
- [jeremy-genkit-pro](../jeremy-genkit-pro/) -- Combine ADK multi-agent coordination with Genkit flows

## Best Practices Enforced

- **Security**: Never hardcode credentials; use Secret Manager or environment variables
- **IAM**: Least-privilege service accounts for all deployments
- **Testing**: Aim for >80% coverage; test happy paths and error cases
- **Error Handling**: Structured error responses, retry with backoff, graceful degradation
- **Code Quality**: Type hints, docstrings, PEP 8 compliance
- **Observability**: Structured logging, Cloud Monitoring, distributed tracing

## License

MIT

## Support

- ADK Documentation: https://google.github.io/adk-docs/
- Issues: https://github.com/jeremylongshore/claude-code-plugins/issues
- Discussions: https://github.com/jeremylongshore/claude-code-plugins/discussions

## Version

2.1.0 (2026) - Full plugin with production agent patterns, testing, and deployment automation
