# Error Handling Reference

## SDK / Authentication Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `ModuleNotFoundError: No module named 'vertexai'` | Vertex AI SDK not installed | `pip install google-cloud-aiplatform[agent_engines]>=1.120.0` |
| `google.auth.exceptions.DefaultCredentialsError` | No application default credentials configured | Run `gcloud auth application-default login` or set `GOOGLE_APPLICATION_CREDENTIALS` |
| `google.api_core.exceptions.PermissionDenied (403)` | Service account or user lacks required IAM roles | Grant `roles/aiplatform.user` and `roles/monitoring.viewer` on the project |
| `google.api_core.exceptions.NotFound (404)` | Agent engine ID or resource name is incorrect | Verify the full resource name: `projects/PROJECT/locations/LOCATION/reasoningEngines/ID`. List engines with `client.agent_engines.list()` |
| `google.api_core.exceptions.InvalidArgument (400)` | Malformed request — wrong location, invalid config | Confirm the location matches where the engine was deployed (e.g., `us-central1`) |

## Agent Engine Retrieval Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `client.agent_engines.get()` returns `None` | Engine was deleted or ID is stale | Re-list engines with `client.agent_engines.list()` to find the current resource name |
| `UNAVAILABLE` / `DEADLINE_EXCEEDED` | Transient network or service issue | Retry with exponential backoff; check [Vertex AI status](https://status.cloud.google.com/) |
| `RESOURCE_EXHAUSTED` | Quota limit hit on Agent Engine API | Check quotas in Cloud Console under IAM & Admin > Quotas; request an increase if needed |

## Common gcloud CLI Misconceptions

**There is no `gcloud` CLI for Agent Engine.** The following commands do NOT exist and will fail:

- `gcloud ai agents describe` / `gcloud ai agents list`
- `gcloud ai reasoning-engines list`
- `gcloud alpha ai agent-engines list`
- `gcloud ai agents update`

All Agent Engine operations must use the Python SDK:

```python
import vertexai

client = vertexai.Client(project="PROJECT_ID", location="LOCATION")

# List all agent engines
for engine in client.agent_engines.list():
    print(engine.name, engine.display_name)

# Get a specific agent engine
engine = client.agent_engines.get(
    name="projects/PROJECT_ID/locations/LOCATION/reasoningEngines/ENGINE_ID"
)

# Create / deploy a new agent engine
from google.adk.agents import Agent
agent = Agent(name="my-agent", model="gemini-2.5-flash")
engine = client.agent_engines.create(agent=agent, config={"display_name": "my-agent"})
```

## A2A Protocol Errors

| Error | Cause | Solution |
|-------|-------|----------|
| AgentCard endpoint returns 404 | Agent not configured for A2A protocol or wrong endpoint URL | Verify A2A is enabled in the agent config; check that `/.well-known/agent-card` path is correct |
| Task API returns 401/403 | Missing or invalid auth token in request header | Include `Authorization: Bearer $(gcloud auth print-access-token)` header |
| Task API returns 500 | Agent crashed while processing the task | Check Cloud Logging for agent error logs; inspect the agent's error handler |
| Status API timeout | Long-running task with no status update mechanism | Implement streaming or polling with reasonable timeout (30-60s) |

## Monitoring and Observability Errors

| Error | Cause | Solution |
|-------|-------|----------|
| Cloud Monitoring returns no data | Monitoring API not enabled or no recent agent traffic | Run `gcloud services enable monitoring.googleapis.com`; generate test traffic first |
| Metrics query returns `INVALID_ARGUMENT` | Incorrect metric type string or filter syntax | Verify metric type with [Metrics Explorer](https://console.cloud.google.com/monitoring/metrics-explorer) |
| Log queries return empty results | Wrong resource type filter or time range | Use `resource.type="aiplatform.googleapis.com/Agent"` and verify timestamps are UTC |
| Cloud Trace shows no spans | OpenTelemetry not configured in the agent | Add Cloud Trace exporter to the agent's OpenTelemetry setup |

## Security Posture Check Errors

| Error | Cause | Solution |
|-------|-------|----------|
| IAM policy query fails | User lacks `resourcemanager.projects.getIamPolicy` permission | Grant `roles/iam.securityReviewer` for read-only IAM inspection |
| VPC-SC perimeter query fails | No organization-level access | VPC-SC queries require org-level permissions; ask an org admin or skip this check |
| Model Armor status unknown | Feature not available in the agent's region | Model Armor availability varies by region; check [region support](https://cloud.google.com/vertex-ai/docs/general/locations) |
| Secret scan false positive | Environment variable names match secret patterns | Add false positive patterns to the exclusion list in the security checker config |

## Code Execution Sandbox Errors

| Error | Cause | Solution |
|-------|-------|----------|
| State TTL rejected (> 14 days) | Agent Engine enforces max 14-day TTL | Set `state_ttl_days` between 1 and 14 |
| Sandbox timeout | Code execution exceeded the configured timeout | Increase timeout or optimize the executed code; check for infinite loops |
| Sandbox OOM (out of memory) | Code execution consumed too much memory | Reduce data size processed in sandbox; increase memory limits if available |
| Sandbox network error | Code tried to make external network calls from isolated sandbox | Sandbox is network-isolated by design; move network calls outside the sandbox |

## Memory Bank Errors

| Error | Cause | Solution |
|-------|-------|----------|
| Memory Bank query slow (> 500ms) | Indexing not enabled or index stale | Enable indexing in Memory Bank config; rebuild index if needed |
| Memory quota exceeded | Too many memories stored without cleanup | Enable auto-cleanup or increase max_memories limit |
| Firestore permission denied | Agent service account lacks Firestore access | Grant `roles/datastore.user` to the agent's service account |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
