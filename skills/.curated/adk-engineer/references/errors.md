# ADK Engineer — Common Errors

## Build and Import Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `ModuleNotFoundError: No module named 'google.adk'` | ADK package not installed or wrong virtual environment active | `pip install google-adk` in the project venv; verify with `python -c "import google.adk"` |
| `ImportError: cannot import name 'Agent' from 'google.adk.agents'` | Outdated ADK version missing the Agent class | `pip install --upgrade google-adk>=0.3.0` |
| `SyntaxError` in agent or tool files | Malformed Python (missing colon, indent error, unclosed bracket) | Run `python -m py_compile src/agent.py` to locate the exact line |
| `AttributeError: 'Agent' object has no attribute 'tools'` | Using wrong Agent constructor signature for the ADK version | Check ADK changelog; `tools=` parameter requires `FunctionTool` wrappers in recent versions |
| `TypeError: __init__() got an unexpected keyword argument 'instruction'` | ADK version uses `instructions` (plural) not `instruction` | Change to `instructions=` or pin to the version matching your code |

## Test Failures

| Error | Cause | Fix |
|-------|-------|-----|
| `pytest: command not found` | pytest not installed in the active environment | `pip install pytest pytest-cov` |
| `FAILED: mock_agent.run.assert_called_once_with(...)` | Agent call signature changed after refactor | Update the mock assertion to match new parameter order or added kwargs |
| `fixture 'tmp_path' not found` | pytest version below 3.9 | `pip install --upgrade pytest>=7.0` |
| Coverage below threshold | New tool code added without corresponding tests | Write tests for each new tool function; target 80%+ line coverage |
| `TimeoutError` in tool tests | Subprocess call to linter/test runner exceeds timeout | Increase `timeout=` parameter or mock the subprocess call in unit tests |

## Runtime and Tool Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `subprocess.TimeoutExpired` in tool execution | External command (linter, test runner) hangs | Add explicit `timeout=` to all `subprocess.run()` calls; default to 30s |
| `FileNotFoundError` from tool function | Target file path does not exist or contains typo | Validate file paths before passing to tools; return structured error with the attempted path |
| `json.JSONDecodeError` parsing tool output | External tool produced non-JSON output (error message, empty string) | Check `result.stdout` is non-empty before `json.loads()`; fall back to raw text on parse failure |
| Tool returns unbounded data | No cap on findings/results causing token bloat | Slice results (e.g., `findings[:10]`) and add a `truncated: true` flag |
| `PermissionError` accessing files | File permissions restrict read/write | Check file permissions with `ls -la`; use `chmod` or run with appropriate user |

## Deployment Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `google.api_core.exceptions.PermissionDenied: 403` | Service account missing `roles/aiplatform.user` | `gcloud projects add-iam-policy-binding PROJECT --member=serviceAccount:SA --role=roles/aiplatform.user` |
| `Agent Engine creation timeout` | Agent package too large or region capacity issue | Reduce package size (exclude test files); try `us-central1` for best availability |
| `INVALID_ARGUMENT: model not supported` | Specified Gemini model not available in target region | Use `gemini-2.5-flash` or `gemini-2.5-pro`; check regional availability in Vertex AI docs |
| `Requirements file parse error` during Agent Engine deploy | Invalid `requirements.txt` format (missing versions, local paths) | Pin all dependencies with `==` versions; remove local path references |
| `VPC Service Controls violation` | Deployment blocked by organization perimeter | Add the deploying service account to the VPC-SC access level; or deploy from within the perimeter |

## Configuration Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `AgentConfig` fields ignored | Config object created but not passed to `create_agent()` | Verify config is passed as argument: `create_agent(config=my_config)` |
| Wrong region for deployment | `region` in config doesn't match gcloud default | Explicitly set `region` in AgentConfig; verify with `gcloud config get compute/region` |
| Model string not recognized | Using full model path instead of short name | Use `gemini-2.5-flash` not `projects/X/locations/Y/publishers/google/models/gemini-2.5-flash` |
| Environment variable not set | Required API key or project ID missing | Export before running: `export GOOGLE_CLOUD_PROJECT=my-project`; use `.env` file with python-dotenv |
| `google.auth.exceptions.DefaultCredentialsError` | Application Default Credentials not configured | Run `gcloud auth application-default login` or set `GOOGLE_APPLICATION_CREDENTIALS` |
| Conflicting dependency versions | Multiple ADK-related packages with incompatible version pins | Create a clean venv: `python -m venv .venv && pip install -r requirements.txt` |

## Orchestration Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `SequentialAgent` skips sub-agents | Sub-agent returns empty response interpreted as completion | Ensure each sub-agent produces non-empty output; add explicit handoff messages |
| `ParallelAgent` race condition | Multiple agents writing to the same state key | Use unique state keys per parallel branch; merge results in a post-processing step |
| `LoopAgent` infinite loop | Exit condition never satisfied by agent output | Set `max_iterations` on LoopAgent; add explicit exit instruction in agent prompt |
| Sub-agent not receiving context | Parent agent context not propagated to child | Pass `session_id` through the orchestrator; verify state sharing configuration |
| Agent ordering wrong in pipeline | Sub-agents list order doesn't match intended sequence | Review `sub_agents=[...]` list; agents execute in list order for SequentialAgent |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
