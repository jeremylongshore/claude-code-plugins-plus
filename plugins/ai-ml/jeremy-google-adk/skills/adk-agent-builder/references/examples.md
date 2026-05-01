# ADK Agent Builder — Usage Examples

## Example 1: Single ReAct Agent — PR Summarizer

**Request**: "Create an ADK agent that summarizes GitHub PRs and suggests test updates."

**What the skill produces**:

```
my-pr-agent/
├── src/
│   ├── agents/
│   │   └── pr_summarizer.py
│   └── tools/
│       ├── github_fetcher.py
│       └── test_analyzer.py
├── tests/
│   ├── test_github_fetcher.py
│   └── test_pr_summarizer.py
├── pyproject.toml
└── README.md
```

**Agent entrypoint** (`src/agents/pr_summarizer.py`):
```python
from google.adk.agents import Agent
from google.adk.tools import Tool
from src.tools.github_fetcher import fetch_pr_diff
from src.tools.test_analyzer import suggest_tests

agent = Agent(
    name="pr-summarizer",
    model="gemini-2.0-flash",
    system_prompt="You summarize PR changes and suggest missing test coverage.",
    tools=[fetch_pr_diff, suggest_tests],
)
```

**Smoke test**: `adk run --prompt "Summarize PR #42 in repo owner/project"`

---

## Example 2: Multi-Agent Team — Research → Write → Review

**Request**: "Build a 3-agent team: researcher finds info, writer drafts content, reviewer checks quality."

**Architecture**: Sequential orchestration (researcher → writer → reviewer)

```python
from google.adk.agents import Agent, SequentialAgent

researcher = Agent(name="researcher", model="gemini-2.0-flash",
    system_prompt="Find relevant information on the given topic.",
    tools=[web_search, doc_reader])

writer = Agent(name="writer", model="gemini-2.0-flash",
    system_prompt="Draft content based on research findings.",
    tools=[text_formatter])

reviewer = Agent(name="reviewer", model="gemini-2.0-flash",
    system_prompt="Review draft for accuracy, clarity, and completeness.",
    tools=[fact_checker])

pipeline = SequentialAgent(
    name="content-pipeline",
    agents=[researcher, writer, reviewer],
)
```

---

## Example 3: Deploy to Vertex AI Agent Engine

**Request**: "Deploy my agent to Agent Engine with health checks."

**Commands produced**:
```bash
# Build and deploy
adk deploy --project=my-gcp-project --region=us-central1 --agent=src/agents/pr_summarizer.py

# Verify deployment
gcloud ai agent-engines list --project=my-gcp-project --region=us-central1

# Test deployed agent
curl -X POST "https://us-central1-aiplatform.googleapis.com/v1/projects/my-gcp-project/locations/us-central1/agents/pr-summarizer:generate" \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Summarize PR #42"}'

# Check logs
gcloud logging read "resource.type=aiplatform.googleapis.com/Agent AND resource.labels.agent_id=pr-summarizer" --limit=20
```

---

## Example 4: Add a Custom Tool

**Request**: "Add a Slack notification tool to my existing agent."

**Tool file** (`src/tools/slack_notifier.py`):
```python
from google.adk.tools import Tool
import os, requests

@Tool(description="Send a message to a Slack channel")
def send_slack_message(channel: str, message: str) -> str:
    webhook_url = os.environ["SLACK_WEBHOOK_URL"]
    response = requests.post(webhook_url, json={"channel": channel, "text": message})
    return f"Sent to {channel}: {response.status_code}"
```

**Register in agent**:
```python
from src.tools.slack_notifier import send_slack_message

agent = Agent(
    name="pr-summarizer",
    tools=[fetch_pr_diff, suggest_tests, send_slack_message],  # Added
)
```

**Environment**: `export SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...`

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
