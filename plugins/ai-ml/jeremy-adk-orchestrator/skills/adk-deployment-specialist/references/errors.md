# Error Handling Reference

## Deployment Failures

### `google.api_core.exceptions.NotFound: 404 Reasoning engine not found`

- **Cause**: The reasoning engine resource name is incorrect or the resource was deleted.
- **Fix**: Verify the resource name with `client.agent_engines.list()` and confirm the project/location match.

### `google.api_core.exceptions.PermissionDenied: 403 Permission denied on resource`

- **Cause**: The service account or user lacks required IAM roles.
- **Fix**: Grant `roles/aiplatform.user` for querying agents, `roles/aiplatform.admin` for creating/deleting. Use `gcloud projects get-iam-policy PROJECT_ID` to audit current bindings.

### `google.api_core.exceptions.InvalidArgument: 400 Invalid agent configuration`

- **Cause**: The agent definition has invalid fields, unsupported model, or malformed tools.
- **Fix**: Verify the model string (e.g., `gemini-2.5-flash`), ensure all tool functions have proper type hints and docstrings, and check that `requirements` list includes all needed packages.

### `google.api_core.exceptions.ResourceExhausted: 429 Quota exceeded`

- **Cause**: Project has hit the Agent Engine quota (default: 10 reasoning engines per project).
- **Fix**: Request quota increase via Cloud Console > IAM & Admin > Quotas, or delete unused agents with `client.agent_engines.delete(name=resource_name)`.

### Deployment hangs or times out

- **Cause**: Large dependency list, network issues, or package build failures in the remote environment.
- **Fix**: Minimize `requirements` to only what the agent needs. Pin exact versions. Check Cloud Build logs via `gcloud builds list --project=PROJECT_ID`.

## Authentication & Authorization Issues

### `google.auth.exceptions.DefaultCredentialsError: Could not automatically determine credentials`

- **Cause**: No Application Default Credentials configured.
- **Fix**: Run `gcloud auth application-default login` for local development, or set `GOOGLE_APPLICATION_CREDENTIALS` to a service account key path. For production, use Workload Identity Federation.

### `google.auth.exceptions.RefreshError: ('invalid_grant: Token has been expired or revoked')`

- **Cause**: Cached credentials are stale or the service account key was rotated.
- **Fix**: Re-authenticate with `gcloud auth application-default login`. For service accounts, generate a new key and update `GOOGLE_APPLICATION_CREDENTIALS`.

### Agent runs but returns permission errors at runtime

- **Cause**: The Agent Engine service agent (the identity the deployed agent runs as) lacks permissions to call downstream APIs (e.g., GKE, Cloud Run).
- **Fix**: Grant the Agent Engine service agent (`service-PROJECT_NUMBER@gcp-sa-aiplatform-re.iam.gserviceaccount.com`) the required roles for the APIs the agent's tools invoke.

## Orchestration Failures

### Sub-agent in SequentialAgent fails mid-pipeline

- **Cause**: One agent in the chain returned an error or produced output the next agent could not process.
- **Fix**: Wrap each sub-agent in error-handling instructions. Add a `try/except` around the orchestrator call. Check which sub-agent failed by inspecting the `events` in the runner response.

### ParallelAgent produces inconsistent results

- **Cause**: Parallel sub-agents share no state by default; if they depend on each other's output, results are non-deterministic.
- **Fix**: Use `SequentialAgent` when ordering matters. Only use `ParallelAgent` for truly independent tasks.

### LoopAgent exceeds max iterations

- **Cause**: The exit condition was never met, or the loop agent's `should_continue` logic has a bug.
- **Fix**: Set `max_iterations` on the `LoopAgent`. Add explicit exit conditions in the agent's instructions. Monitor iteration count in logs.

## SDK & Import Errors

### `ImportError: cannot import name 'Agent' from 'google.adk'`

- **Cause**: Using the wrong import path.
- **Fix**: The correct import is `from google.adk.agents import Agent`. Other common imports:
  - `from google.adk.agents import SequentialAgent, ParallelAgent, LoopAgent`
  - `from google.adk.runners import Runner`
  - `from google.adk.sessions import VertexAiSessionService`
  - `from google.adk.tools import FunctionTool`

### `ModuleNotFoundError: No module named 'google.adk'`

- **Cause**: ADK SDK not installed or wrong Python environment.
- **Fix**: Install with `pip install google-adk>=1.15.1`. Verify with `python -c "import google.adk; print(google.adk.__version__)"`.

## Agent Engine Management (No gcloud CLI)

There is no `gcloud ai agents` or `gcloud alpha ai agent-engines` CLI. All Agent Engine management is done via the Python SDK:

```python
import vertexai

client = vertexai.Client(project="PROJECT_ID", location="us-central1")

# List agents
agents = client.agent_engines.list()

# Get a specific agent
agent = client.agent_engines.get(
    name="projects/PROJECT/locations/LOC/reasoningEngines/ID"
)

# Create/deploy an agent
remote = client.agent_engines.create(agent_engine=my_agent, requirements=[...])

# Delete an agent
client.agent_engines.delete(name=agent.resource_name)
```

## A2A Protocol Errors

### AgentCard not found at `/.well-known/agent-card`

- **Cause**: The agent does not expose an A2A-compliant AgentCard, or the URL is wrong.
- **Fix**: Verify the agent was deployed with A2A support. The AgentCard endpoint is `/.well-known/agent-card` (note: no trailing slash). Ensure the agent framework generates this endpoint.

### `tasks/send` returns 405 Method Not Allowed

- **Cause**: The agent endpoint does not support the A2A task submission method.
- **Fix**: Confirm the agent was built with A2A protocol support (`a2a-sdk`). Check that the server handles POST to `/tasks/send` with JSON-RPC 2.0 format.

### Task polling returns stale status

- **Cause**: Eventual consistency or caching in the agent's task store.
- **Fix**: Implement exponential backoff in polling (start at 2s, max 30s). Use the task's `updatedAt` timestamp to detect stale responses.

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
