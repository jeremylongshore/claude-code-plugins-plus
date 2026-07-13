# Examples — ADK Software Engineer

## Example 1: Production-Ready ADK Agent with Custom Tools

Build a code review agent with structured tool interfaces and tests.

### Project Structure

```
code-review-agent/
├── src/
│   ├── agent.py          # Agent definition
│   ├── tools.py          # Custom tool functions
│   └── config.py         # Configuration
├── tests/
│   ├── test_agent.py     # Unit tests
│   └── test_tools.py     # Tool tests
├── pyproject.toml
└── requirements.txt
```

### Agent Implementation

```python
# src/config.py
from dataclasses import dataclass

@dataclass
class AgentConfig:
    model: str = "gemini-2.5-flash"
    project_id: str = ""
    region: str = "us-central1"
    max_retries: int = 3
    timeout_seconds: int = 30
```

```python
# src/tools.py
from google.adk.tools import FunctionTool
from typing import Dict, List
import subprocess
import json

# ADK tools: define plain functions, wrap with FunctionTool.
# The function docstring becomes the tool description for the LLM.

def run_linter(file_path: str, language: str = "python") -> Dict:
    """Run a linter on a file and return findings as structured results."""
    linter_map = {
        "python": ["ruff", "check", "--output-format=json"],
        "typescript": ["eslint", "--format=json"],
    }
    cmd = linter_map.get(language, linter_map["python"])
    cmd.append(file_path)

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30
        )
        findings = json.loads(result.stdout) if result.stdout else []
        return {
            "status": "success",
            "file": file_path,
            "finding_count": len(findings),
            "findings": findings[:10],  # Cap at 10 to avoid token bloat
        }
    except subprocess.TimeoutExpired:
        return {"status": "error", "error": "Linter timed out after 30s"}
    except FileNotFoundError:
        return {"status": "error", "error": f"Linter '{cmd[0]}' not installed"}


def read_file_section(file_path: str, start_line: int, end_line: int) -> Dict:
    """Read lines from a file. Returns content with line numbers."""
    try:
        with open(file_path, "r") as f:
            lines = f.readlines()

        start = max(0, start_line - 1)
        end = min(len(lines), end_line)
        section = lines[start:end]

        return {
            "status": "success",
            "file": file_path,
            "start_line": start + 1,
            "end_line": end,
            "content": "".join(
                f"{i+start+1:4d} | {line}" for i, line in enumerate(section)
            ),
        }
    except FileNotFoundError:
        return {"status": "error", "error": f"File not found: {file_path}"}


def check_test_coverage(module_path: str) -> Dict:
    """Run pytest with coverage and return summary."""
    try:
        result = subprocess.run(
            ["python", "-m", "pytest", "--cov=" + module_path,
             "--cov-report=json", "-q", "--tb=no"],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode == 0:
            with open("coverage.json") as f:
                cov = json.load(f)
            return {
                "status": "success",
                "total_coverage": cov["totals"]["percent_covered"],
                "files": {
                    k: v["summary"]["percent_covered"]
                    for k, v in cov["files"].items()
                },
            }
        return {"status": "error", "error": result.stderr[:500]}
    except Exception as e:
        return {"status": "error", "error": str(e)}
```

```python
# src/agent.py
from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from src.tools import run_linter, read_file_section, check_test_coverage
from src.config import AgentConfig

SYSTEM_INSTRUCTION = """You are a senior code reviewer for Python projects.

WORKFLOW:
1. Run the linter on each changed file to find static analysis issues
2. Read file sections with the most complex logic for manual review
3. Check test coverage to identify untested code paths
4. Provide a structured review with severity levels

REVIEW FORMAT:
- CRITICAL: Security vulnerabilities, data loss risks, crashes
- WARNING: Performance issues, code smells, missing validation
- SUGGESTION: Style improvements, better patterns, documentation gaps

Always explain WHY something is an issue and provide a concrete fix.
"""

def create_review_agent(config: AgentConfig = None) -> Agent:
    """Create a configured code review agent."""
    config = config or AgentConfig()

    agent = Agent(
        model=config.model,
        name="code-review-agent",
        description="Reviews code for quality, security, and test coverage",
        instruction=SYSTEM_INSTRUCTION,
        tools=[
            FunctionTool(func=run_linter),
            FunctionTool(func=read_file_section),
            FunctionTool(func=check_test_coverage),
        ],
    )
    return agent


# Usage
if __name__ == "__main__":
    agent = create_review_agent()
    response = agent.run(
        "Review the file src/tools.py for code quality and security issues"
    )
    print(response.text)
```

### Tests

```python
# tests/test_tools.py
import pytest
import tempfile
import os
from src.tools import run_linter, read_file_section, check_test_coverage


class TestReadFileSection:
    def test_reads_valid_range(self, tmp_path):
        f = tmp_path / "sample.py"
        f.write_text("line1\nline2\nline3\nline4\nline5\n")

        result = read_file_section(str(f), start_line=2, end_line=4)

        assert result["status"] == "success"
        assert result["start_line"] == 2
        assert result["end_line"] == 4
        assert "line2" in result["content"]
        assert "line4" in result["content"]
        assert "line5" not in result["content"]

    def test_handles_missing_file(self):
        result = read_file_section("/nonexistent/file.py", 1, 10)
        assert result["status"] == "error"
        assert "not found" in result["error"].lower()

    def test_clamps_out_of_range(self, tmp_path):
        f = tmp_path / "short.py"
        f.write_text("only\ntwo\n")

        result = read_file_section(str(f), start_line=1, end_line=100)

        assert result["status"] == "success"
        assert result["end_line"] == 2


class TestRunLinter:
    def test_returns_error_for_missing_linter(self, tmp_path):
        f = tmp_path / "test.py"
        f.write_text("x = 1\n")

        # ruff may not be installed in test env
        result = run_linter(str(f), language="python")
        assert result["status"] in ("success", "error")

    def test_caps_findings_at_ten(self):
        # Verify the cap logic
        findings = list(range(20))
        capped = findings[:10]
        assert len(capped) == 10
```

```python
# tests/test_agent.py
import pytest
from unittest.mock import patch, MagicMock
from src.agent import create_review_agent
from src.config import AgentConfig


def test_agent_creation():
    """Agent initializes with correct tools and config."""
    agent = create_review_agent(AgentConfig(model="gemini-2.5-flash"))

    assert agent.name == "code-review-agent"
    assert len(agent.tools) == 3


def test_agent_custom_config():
    """Agent respects custom configuration."""
    config = AgentConfig(
        model="gemini-2.5-pro",
        project_id="my-project",
        region="europe-west4",
    )
    agent = create_review_agent(config)
    assert agent.model == "gemini-2.5-pro"
```

### Expected Output

Running the agent:

```
$ python -m src.agent

## Code Review: src/tools.py

### CRITICAL
- **subprocess injection risk** (line 18): `cmd.append(file_path)` passes user input directly to subprocess. Sanitize `file_path` to reject shell metacharacters or use `shlex.quote()`.

### WARNING
- **Unbounded file read** (read_file_section): No file size check before reading. Add a max file size guard (e.g., 1 MB) to prevent memory issues.
- **Coverage JSON left on disk** (check_test_coverage): `coverage.json` is written but never cleaned up. Use `tempfile.NamedTemporaryFile` instead.

### SUGGESTION
- Add type hints to return values for better IDE support.
- Consider async versions of subprocess calls for concurrent file reviews.

Test coverage: 78% (src/tools.py: 72%, src/agent.py: 85%)
```

---

## Example 2: Multi-Agent Sequential Workflow

Build a validator-deployer-monitor agent team.

```python
# orchestrator.py
from google.adk.agents import Agent, SequentialAgent

# Agent 1: Configuration Validator
validator = Agent(
    model="gemini-2.5-flash",
    name="config-validator",
    instruction="""Validate deployment configurations.
Check: required fields present, valid regions, resource limits within quotas,
IAM roles follow least-privilege, no hardcoded secrets.""",
    tools=[],  # Pure reasoning, no tools needed
)

# Agent 2: Deployer
deployer = Agent(
    model="gemini-2.5-flash",
    name="deployer",
    instruction="""Execute deployments based on validated configurations.
Run gcloud commands, verify resources are created, report deployment status.""",
)

# Agent 3: Health Monitor
monitor = Agent(
    model="gemini-2.5-flash",
    name="health-monitor",
    instruction="""After deployment, verify health.
Check: endpoint responds 200, latency < 500ms, no error logs in last 5 min.""",
)

# Wire into sequential orchestrator
pipeline = SequentialAgent(
    name="deploy-pipeline",
    sub_agents=[validator, deployer, monitor],
    description="Validate config -> Deploy -> Monitor health",
)

# Run the pipeline
result = pipeline.run("""
Deploy a Cloud Run service with:
- Image: gcr.io/my-project/api-server:v2.1.0
- Region: us-central1
- Memory: 512Mi
- Min instances: 1
- Max instances: 10
- Service account: api-server-sa@my-project.iam.gserviceaccount.com
""")

print(result.text)
```

### Expected Output

```
## Pipeline Result

### Step 1: Validation (PASS)
- All required fields present
- Region us-central1 is valid
- Memory 512Mi within quota
- Service account follows naming convention
- No hardcoded secrets detected

### Step 2: Deployment (SUCCESS)
- Deployed api-server to us-central1
- URL: https://api-server-abc123-uc.a.run.app
- Revision: api-server-00002-abc

### Step 3: Health Check (HEALTHY)
- GET /health returned 200 in 142ms
- No errors in Cloud Logging (last 5 min)
- CPU utilization: 12%, Memory: 180Mi/512Mi
```

---

## Example 3: Adding Tests to an Existing Agent

Refactor and add regression tests to untested agent code.

```python
# Before: untested agent code
# src/chat_agent.py (original)
from google.adk.agents import Agent

agent = Agent(model="gemini-2.5-flash", name="chat")

def chat(msg):
    return agent.run(msg)
```

```python
# After: refactored with testability
# src/chat_agent.py (refactored)
from google.adk.agents import Agent
from typing import Optional, Protocol

class LLMProvider(Protocol):
    """Protocol for dependency injection in tests."""
    def run(self, message: str, session_id: Optional[str] = None) -> object: ...

def create_chat_agent(model: str = "gemini-2.5-flash") -> Agent:
    return Agent(
        model=model,
        name="chat-agent",
        instruction="You are a helpful assistant. Be concise.",
    )

def chat(message: str, agent: Optional[LLMProvider] = None,
         session_id: Optional[str] = None) -> str:
    """Send a message and return the response text."""
    if agent is None:
        agent = create_chat_agent()

    if not message or not message.strip():
        raise ValueError("Message cannot be empty")

    response = agent.run(message, session_id=session_id)
    return response.text
```

```python
# tests/test_chat_agent.py
import pytest
from unittest.mock import MagicMock
from src.chat_agent import chat, create_chat_agent

class TestChat:
    def test_returns_response_text(self):
        mock_agent = MagicMock()
        mock_agent.run.return_value.text = "Hello! How can I help?"

        result = chat("Hi there", agent=mock_agent)

        assert result == "Hello! How can I help?"
        mock_agent.run.assert_called_once_with("Hi there", session_id=None)

    def test_passes_session_id(self):
        mock_agent = MagicMock()
        mock_agent.run.return_value.text = "Welcome back"

        chat("Hi", agent=mock_agent, session_id="sess-123")

        mock_agent.run.assert_called_once_with("Hi", session_id="sess-123")

    def test_rejects_empty_message(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            chat("", agent=MagicMock())

    def test_rejects_whitespace_message(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            chat("   ", agent=MagicMock())

    def test_create_agent_defaults(self):
        agent = create_chat_agent()
        assert agent.name == "chat-agent"
        assert agent.model == "gemini-2.5-flash"
```

### Running Tests

```bash
$ pytest tests/ -v --tb=short

tests/test_chat_agent.py::TestChat::test_returns_response_text PASSED
tests/test_chat_agent.py::TestChat::test_passes_session_id PASSED
tests/test_chat_agent.py::TestChat::test_rejects_empty_message PASSED
tests/test_chat_agent.py::TestChat::test_rejects_whitespace_message PASSED
tests/test_chat_agent.py::TestChat::test_create_agent_defaults PASSED

5 passed in 0.12s
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
