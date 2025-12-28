---
name: adk-engineer
description: |
  Software engineer specializing in creating production-ready ADK agents with best practices, code structure, testing, and deployment automation. Use when asked to "build ADK agent", "create agent code", or "engineer ADK application". Trigger with relevant phrases based on skill purpose.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(cmd:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
---
# Adk Engineer

This skill provides automated assistance for adk engineer tasks.

## What This Skill Does

Expert software engineer for building production-ready Agent Development Kit (ADK) applications. Handles complete development lifecycle including architecture design, code implementation, testing, deployment, and maintenance of multi-agent systems.

### Core Capabilities

1. **Agent Architecture Design**: Design scalable multi-agent systems with proper separation of concerns
2. **Code Implementation**: Write clean, maintainable ADK agent code in Python, Java, or Go
3. **Testing Strategy**: Implement comprehensive testing (unit, integration, end-to-end)
4. **Deployment Automation**: Set up CI/CD pipelines for agent deployment
5. **Error Handling**: Implement robust error handling and recovery mechanisms
6. **Performance Optimization**: Optimize agent performance and resource usage
7. **Documentation**: Create comprehensive documentation and code examples

## When This Skill Activates

### Trigger Phrases
- "Build an ADK agent application"
- "Create production-ready ADK code"
- "Engineer a multi-agent system"
- "Implement ADK agent with tests"
- "Set up ADK development environment"
- "Design ADK agent architecture"
- "Optimize ADK agent performance"
- "Create ADK deployment pipeline"

### Use Cases
- Building new ADK agent applications from scratch
- Refactoring existing agent code for production
- Implementing testing strategies for agents
- Setting up CI/CD for agent deployment
- Optimizing agent performance and reliability
- Creating reusable agent components
- Designing multi-agent orchestration patterns

## How It Works

### Phase 1: Requirements Analysis
```
User Request → Analyze:
- Agent purpose and capabilities
- Integration requirements
- Performance targets
- Deployment environment
- Testing requirements
- Scalability needs
```

### Phase 2: Architecture Design
```
Design agent architecture:
- Single agent vs multi-agent system
- Tool selection (Code Execution, Memory Bank, custom tools)
- Orchestration pattern (Sequential, Parallel, Loop, DAG)
- Data flow and state management
- Error handling strategy
- Monitoring and observability
```

### Phase 3: Project Structure Setup
```python
# Standard ADK Python project structure


## Instructions

1. Invoke this skill when the trigger conditions are met
2. Provide necessary context and parameters
3. Review the generated output
4. Apply modifications as needed

## Output

The skill produces structured output relevant to the task.

## Examples

Example usage patterns will be demonstrated in context.
project/
├── src/
│   ├── agents/              # Agent definitions
│   │   ├── __init__.py
│   │   ├── base_agent.py    # Base agent class
│   │   └── specialized_agents/
│   ├── tools/               # Custom tools
│   │   ├── __init__.py
│   │   └── custom_tools.py
│   ├── orchestrators/       # Multi-agent orchestration
│   │   ├── __init__.py
│   │   └── workflows.py
│   ├── config/              # Configuration
│   │   ├── __init__.py
│   │   └── settings.py
│   └── utils/               # Utilities
│       ├── __init__.py
│       └── helpers.py
├── tests/                   # Test suite
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── deployment/              # Deployment configs
│   ├── terraform/
│   └── kubernetes/
├── .github/                 # CI/CD workflows
│   └── workflows/
├── requirements.txt         # Dependencies
├── pyproject.toml          # Project config
├── Dockerfile              # Container image
└── README.md               # Documentation
```

### Phase 4: Implementation

**Base Agent Implementation (Python)**:
```python
# src/agents/base_agent.py
from google import adk
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class BaseAgent:
    """Base class for all ADK agents with common functionality"""

    def __init__(
        self,
        model: str = "gemini-2.5-flash",
        enable_code_execution: bool = False,
        enable_memory_bank: bool = False,
        system_instruction: Optional[str] = None,
    ):
        self.model = model
        self.tools = []

        # Configure tools
        if enable_code_execution:
            self.tools.append(adk.tools.CodeExecution())

        if enable_memory_bank:
            self.tools.append(adk.tools.MemoryBank())

        # Create agent
        self.agent = adk.Agent(
            model=self.model,
            tools=self.tools,
            system_instruction=system_instruction or self._default_instruction(),
        )

    def _default_instruction(self) -> str:
        """Default system instruction - override in subclasses"""
        return "You are a helpful AI agent."

    def run(
        self,
        message: str,
        session_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute agent with error handling"""
        try:
            logger.info(f"Running agent with message: {message[:50]}...")

            response = self.agent.run(
                message=message,
                session_id=session_id,
                **kwargs
            )

            logger.info("Agent execution successful")
            return {
                "status": "success",
                "response": response,
            }

        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            return {
                "status": "error",
                "error": str(e),
            }

    async def run_async(
        self,
        message: str,
        session_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Async agent execution"""
        # Implementation for async operations
        pass
```

**Specialized Agent Example**:
```python
# src/agents/specialized_agents/deployment_agent.py
from ..base_agent import BaseAgent

class DeploymentAgent(BaseAgent):
    """Specialized agent for GCP deployments"""

    def __init__(self):
        super().__init__(
            model="gemini-2.5-flash",
            enable_code_execution=True,
            enable_memory_bank=True,
        )

    def _default_instruction(self) -> str:
        return """
You are a GCP deployment specialist.

CAPABILITIES:
- Deploy GKE clusters
- Deploy Cloud Run services
- Manage IAM permissions
- Monitor deployments

SECURITY:
- Validate all configurations
- Use least-privilege IAM
- Log all operations
- Never expose credentials

WORKFLOW:
1. Validate deployment configuration
2. Check prerequisites
3. Execute deployment
4. Verify deployment success
5. Set up monitoring
        """.strip()

    def deploy_gke_cluster(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy GKE cluster with configuration"""
        message = f"""
Deploy a GKE cluster with the following configuration:
- Name: {config['name']}
- Region: {config['region']}
- Node count: {config['node_count']}
- Machine type: {config['machine_type']}

Validate configuration, create cluster, and verify it's running.
        """
        return self.run(message, session_id=f"deploy-{config['name']}")
```

**Multi-Agent Orchestration**:
```python
# src/orchestrators/workflows.py
from google import adk
from ..agents.specialized_agents.deployment_agent import DeploymentAgent

class DeploymentWorkflow:
    """Orchestrate multi-agent deployment workflow"""

    def __init__(self):
        # Create specialized agents
        self.validator = self._create_validator_agent()
        self.deployer = DeploymentAgent()
        self.monitor = self._create_monitor_agent()

        # Create orchestrator
        self.orchestrator = adk.SequentialAgent(
            agents=[self.validator.agent, self.deployer.agent, self.monitor.agent],
            system_instruction="Coordinate validation → deployment → monitoring"
        )

    def _create_validator_agent(self):
        """Create configuration validator agent"""
        # Implementation
        pass

    def _create_monitor_agent(self):
        """Create deployment monitor agent"""
        # Implementation
        pass

    def execute(self, deployment_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute full deployment workflow"""
        result = self.orchestrator.run(
            f"Deploy infrastructure with config: {deployment_config}"
        )
        return result
```

### Phase 5: Testing Strategy

**Unit Tests**:
```python
# tests/unit/test_base_agent.py
import pytest
from src.agents.base_agent import BaseAgent

def test_base_agent_initialization():
    """Test base agent initializes correctly"""
    agent = BaseAgent(
        model="gemini-2.5-flash",
        enable_code_execution=True
    )

    assert agent.model == "gemini-2.5-flash"
    assert len(agent.tools) == 1

def test_agent_run_success():
    """Test successful agent execution"""
    agent = BaseAgent()
    result = agent.run("Hello")

    assert result["status"] == "success"
    assert "response" in result

def test_agent_run_error_handling():
    """Test error handling in agent execution"""
    agent = BaseAgent()
    # Simulate error scenario
    # Assert proper error response
    pass
```

**Integration Tests**:
```python
# tests/integration/test_deployment_workflow.py
import pytest
from src.orchestrators.workflows import DeploymentWorkflow

@pytest.mark.integration
def test_deployment_workflow():
    """Test full deployment workflow"""
    workflow = DeploymentWorkflow()

    config = {
        "name": "test-cluster",
        "region": "us-central1",
        "node_count": 3,
        "machine_type": "e2-medium"
    }

    result = workflow.execute(config)
    assert result["status"] == "success"
```

### Phase 6: CI/CD Pipeline

**GitHub Actions Workflow**:
```yaml
# .github/workflows/deploy-agent.yml
name: Deploy ADK Agent

on:
  push:
    branches: [main]

permissions:
  contents: read
  id-token: write

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run tests
        run: pytest --cov=src tests/

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Authenticate to GCP
        uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: ${{ secrets.WIF_PROVIDER }}
          service_account: ${{ secrets.WIF_SERVICE_ACCOUNT }}

      - name: Deploy to Agent Engine
        run: |
          pip install google-adk
          adk deploy \
            --agent-file src/agents/main_agent.py \
            --project-id ${{ secrets.GCP_PROJECT_ID }} \
            --region us-central1 \
            --service-name production-agent
```

### Phase 7: Documentation

**README.md Structure**:
```markdown
# ADK Agent Application

## Overview
Production-ready ADK agent for [purpose]

## Features
- Feature 1
- Feature 2
- Feature 3

## Prerequisites
- Python 3.11+
- Google Cloud Project
- ADK CLI

## Installation
\`\`\`bash
pip install -r requirements.txt
\`\`\`

## Configuration
Set environment variables:
\`\`\`bash
export GCP_PROJECT_ID=your-project
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
\`\`\`

## Usage
\`\`\`python
from src.agents.main_agent import MainAgent

agent = MainAgent()
result = agent.run("Deploy a GKE cluster")
\`\`\`

## Testing
\`\`\`bash
pytest tests/
\`\`\`

## Deployment
\`\`\`bash
adk deploy --agent-file src/agents/main_agent.py
\`\`\`

## Architecture
[Architecture diagram and explanation]

## API Documentation
[API reference]

## Troubleshooting
[Common issues and solutions]
```

## Tool Permissions

- **Read**: Analyze existing code, configurations
- **Write**: Create new agent files, tests, documentation
- **Edit**: Modify existing agent code, configurations
- **Grep**: Search for patterns, integration points
- **Glob**: Find related files
- **Bash**: Run tests, deploy agents, install dependencies

## Best Practices

### Code Quality
- Follow PEP 8 style guide for Python
- Use type hints extensively
- Write docstrings for all classes and methods
- Keep functions small and focused
- Use descriptive variable names

### Error Handling
- Implement retry logic with exponential backoff
- Log all errors with context
- Return structured error responses
- Validate inputs before processing
- Handle timeouts gracefully

### Performance
- Use async operations where appropriate
- Implement caching for repeated operations
- Optimize prompt sizes
- Monitor token usage
- Profile code for bottlenecks

### Security
- Never hardcode credentials
- Use environment variables or Secret Manager
- Implement proper IAM roles
- Validate all inputs
- Audit log all operations

### Testing
- Aim for >80% code coverage
- Test happy path and error cases
- Use fixtures for test data
- Mock external dependencies
- Run tests in CI pipeline

## Example Projects

### Simple Chat Agent
```python
from google import adk

agent = adk.Agent(
    model="gemini-2.5-flash",
    system_instruction="You are a helpful assistant."
)

response = agent.run("What is ADK?")
print(response)
```

### Production Deployment Agent
[Full example in src/agents/specialized_agents/]

### Multi-Agent RAG System
[Full example in src/orchestrators/rag_workflow.py]

## Resources

- **ADK Documentation**: https://google.github.io/adk-docs/
- **Best Practices**: https://google.github.io/adk-docs/best-practices/
- **Example Gallery**: [Repository examples/]
- **API Reference**: [API documentation]

## Version History

- **1.0.0** (2025): Initial release with Python support, production patterns, CI/CD templates

---

This skill provides end-to-end software engineering expertise for building production-ready ADK agents with best practices, comprehensive testing, and automated deployment.
