# ARD: ADK Engineer

> Part of [Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)

## System Context

The ADK Engineer skill operates within a developer's local repository and optionally interacts with Google Cloud for deployment. It sits between the developer's requirements and production-ready ADK agent code, bridging the gap between intent and shippable implementation. The skill understands ADK's agent hierarchy (Agent, SequentialAgent, ParallelAgent, LoopAgent), tool system (FunctionTool wrappers), and deployment surface (local execution vs Vertex AI Agent Engine).

```
Developer Request
       ↓
[ADK Engineer Skill]
  ├── Reads: existing project files, configs, tests, requirements.txt
  ├── Writes: agent code, tool modules, tests, deploy scripts, config
  ├── Calls: local test runners, ADK CLI, gcloud (optional)
  └── References: ADK docs, Agent Engine API, Gemini model catalog
       ↓
Production ADK Agent (local or Agent Engine)
  ├── Agent entrypoint with system instruction
  ├── FunctionTool modules with structured returns
  ├── Test suite (unit + integration)
  └── Deployment artifacts (requirements.txt, deploy script)
```

## Data Flow

1. **Input**: User request specifying agent goals, tool surface, orchestration pattern, latency/cost constraints, and deployment target (local vs Agent Engine)
2. **Processing**: Analyze existing project structure via Glob/Grep, scaffold or patch agent entrypoints and tool modules, generate regression tests, validate with local test runner, and produce deployment configuration when requested
3. **Output**: Agent source files (Python/Java/Go), tool implementations with input validation, test suites, a validation checklist, and optional deployment commands for Vertex AI Agent Engine

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Incremental tool addition | One tool at a time with tests | Prevents regressions and keeps review surface small |
| Structured error responses | All tools return `{status, error/data}` dicts | Enables consistent error handling across tools and agents |
| Protocol-based DI for testing | Python Protocol classes for agent mocking | Allows unit testing without live LLM calls or network access |
| Sequential orchestration default | SequentialAgent for multi-agent flows | Simplest pattern with predictable debugging; upgrade to Parallel/Loop only when needed |
| Model selection guidance | Gemini 2.5 Flash default, Pro for reasoning | Flash for throughput and cost; Pro only when task complexity demands it |
| Config dataclass pattern | Python `@dataclass` for AgentConfig | Type-safe configuration; IDE autocomplete; easy to pass and test |
| System instruction as constant | Separate `SYSTEM_INSTRUCTION` string | Visible, reviewable, and testable prompt; not buried inside Agent constructor |
| Subprocess timeout enforcement | Explicit `timeout=` on all subprocess calls | Prevents hung tool executions from blocking the agent indefinitely |

## Tool Usage Pattern

| Tool | Purpose |
|------|---------|
| Read | Inspect existing agent code, configs, and test files to understand current state |
| Write | Create new agent entrypoints, tool modules, config files, and test suites |
| Edit | Patch existing files — add tools, fix bugs, refactor structure |
| Grep | Search for patterns across the codebase (imports, API usage, error handling) |
| Glob | Discover project layout — find all Python files, test files, config files |
| Bash(cmd:*) | Run test suites, linters, ADK CLI commands, and optional gcloud deployments |

## Error Handling Strategy

| Error Class | Detection | Recovery |
|------------|-----------|----------|
| Build/import failures | Non-zero exit from `python -m py_compile` or import errors in test output | Isolate the failing module, fix imports or syntax, re-run build |
| Test failures | pytest exit code != 0 or specific test case FAILED lines | Read failure output, fix the root cause, add a regression test for the fix |
| Tool runtime errors | Structured `{status: "error"}` responses from tool functions | Log the error context, apply retry with backoff for transient failures, surface clear messages for permanent failures |
| Deployment failures | gcloud or Agent Engine SDK returning non-zero or error JSON | Parse the error message, check IAM permissions, verify API enablement, and suggest least-privilege fixes |
| Model quota/timeout | 429 or DEADLINE_EXCEEDED from Gemini API | Implement exponential backoff with jitter; suggest model downgrade (Pro to Flash) or quota increase |

## Extension Points

- Custom tool functions: users add new `FunctionTool` wrappers following the structured return pattern established in `tools.py`
- Orchestration patterns: swap SequentialAgent for ParallelAgent or LoopAgent by changing the pipeline definition in `orchestrator.py`
- Model override: change the model string in AgentConfig to target different Gemini variants (Flash, Pro, Ultra) or third-party providers
- Deployment targets: extend from local/Agent Engine to Cloud Run or GKE by adding deployment config generators in `deploy/`
- Test fixtures: add pytest fixtures in `conftest.py` for common agent/tool mocking patterns
- Session management: integrate Memory Bank for stateful multi-turn conversations by adding session ID tracking
- Observability: add OpenTelemetry tracing spans around tool calls for production debugging
- Cost tracking: instrument token usage per agent call to enable cost attribution and budget alerts
