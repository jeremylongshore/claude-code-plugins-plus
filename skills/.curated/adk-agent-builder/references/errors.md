# ADK Agent Builder — Common Errors

## Import & Dependency Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `ModuleNotFoundError: No module named 'google.adk'` | `google-adk` not installed | `pip install google-adk` |
| `ImportError: cannot import name 'Agent'` | Wrong ADK version or stale install | `pip install --upgrade google-adk` |
| `Python 3.9 not supported` | ADK requires 3.10+ | Use `pyenv` or update system Python |
| `Dependency conflict with langchain` | Both packages modify `google.cloud` namespace | Use separate virtual environments |

## GCP Authentication Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `google.auth.exceptions.DefaultCredentialsError` | No application default credentials | `gcloud auth application-default login` |
| `403 Forbidden: Vertex AI API` | Service account lacks `aiplatform.user` role | `gcloud projects add-iam-policy-binding PROJECT --member=serviceAccount:SA --role=roles/aiplatform.user` |
| `403: Vertex AI API has not been used in project` | API not enabled | `gcloud services enable aiplatform.googleapis.com` |
| `Permission denied on bucket` | Agent Engine needs GCS access | Grant `storage.objectViewer` to the Agent Engine service account |

## Agent Engine Deployment Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `adk deploy: command not found` | ADK CLI not in PATH | `pip install google-adk[cli]` or check PATH |
| `Quota exceeded for Agent Engine` | Region quota limit | Try `us-central1` (highest quota) or request increase |
| `Build failed: requirements.txt not found` | Missing dependency file | Ensure `requirements.txt` or `pyproject.toml` in project root |
| `Agent failed health check after deploy` | Agent crashes on startup | Check logs: `gcloud logging read "resource.type=aiplatform.googleapis.com/Agent"` |
| `Timeout during deployment` | Large container image or slow build | Reduce dependencies, use `--timeout=600` flag |

## Tool & Runtime Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `Tool 'search' not registered` | Tool not added to agent's tool list | Add tool to `tools=[]` parameter in Agent constructor |
| `RateLimitError from tool API` | External API rate limit hit | Add `tenacity` retry with exponential backoff |
| `Agent loop exceeded max_turns` | Agent stuck in reasoning loop | Set `max_turns` parameter, add exit conditions to system prompt |
| `JSON decode error in tool response` | Tool returning non-JSON | Wrap tool output in structured response format |

## Multi-Agent Orchestration Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `Circular dependency in agent graph` | Agent A delegates to B, B delegates to A | Review orchestration topology, use DAG pattern |
| `SequentialAgent: step 2 failed` | Upstream agent produced unexpected output | Add output validation between pipeline stages |
| `ParallelAgent: timeout on subtask` | One parallel agent hung | Set per-agent `timeout` parameter |
| `Orchestrator received empty response` | Sub-agent returned nothing | Add fallback response in sub-agent's system prompt |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
