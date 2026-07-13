# ARD: ADK Agent Builder

> Part of [Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)

## System Context

The ADK Agent Builder operates within the Google Cloud AI ecosystem. It generates project scaffolds that target the `google-adk` SDK and optionally deploy to Vertex AI Agent Engine.

```
Developer (Claude Code)
    │
    ▼
ADK Agent Builder Skill
    │
    ├── Reads: project context, existing code, user requirements
    ├── Generates: agent scaffold (src/agents/, src/tools/, tests/)
    └── Optionally deploys: adk deploy → Vertex AI Agent Engine
                                            │
                                            ├── IAM (Service Account, roles)
                                            ├── Cloud Build (container image)
                                            └── Agent Engine Runtime (serving)
```

## Data Flow

1. **Input**: User describes the agent they want (purpose, tools needed, single vs multi-agent)
2. **Architecture selection**: Skill determines ReAct (single) or orchestrated (multi-agent) based on complexity
3. **Scaffold generation**: Creates directory structure, agent entrypoint, tool registry, config, tests
4. **Tool wiring**: Connects requested tools (APIs, databases, search) with credential management
5. **Validation**: Runs smoke test prompt against local agent to verify it works
6. **Deployment** (optional): Generates `adk deploy` command + post-deploy health checks

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| SDK | Google ADK over LangChain/CrewAI | Native GCP integration, Agent Engine deployment, Google-maintained |
| Agent pattern | ReAct (reasoning + acting) | Proven pattern for tool-using agents, ADK's primary paradigm |
| Multi-agent | Sequential/Parallel/Loop | ADK's built-in orchestration patterns, no custom framework needed |
| Tool registry | Centralized `src/tools/` | Single place to add/remove tools, clear dependency graph |
| Credentials | Environment variables + Secret Manager | Never hardcoded, works in local dev and Agent Engine |
| Testing | Unit tests + smoke prompts | Unit tests for tool logic, smoke prompts for end-to-end agent behavior |

## Tool Usage Pattern

| Tool | Purpose |
|------|---------|
| `Read` | Examine existing project files, understand codebase context |
| `Write` | Create scaffold files (agent code, configs, tests) |
| `Edit` | Modify existing files (add tools to registry, update config) |
| `Grep` | Find existing patterns, check for conflicts |
| `Bash(cmd:*)` | Run `adk deploy`, `pip install`, `python -m pytest`, smoke tests |

## Error Handling Strategy

| Error Class | Detection | Recovery |
|------------|-----------|----------|
| Missing `google-adk` | ImportError on scaffold validation | Provide `pip install google-adk` command |
| GCP auth failure | `gcloud auth` check before deploy | Guide through `gcloud auth application-default login` |
| Missing IAM roles | 403 on Agent Engine API | Identify exact role needed, provide `gcloud` command |
| Vertex AI not enabled | API disabled error | Provide `gcloud services enable` command |
| Tool credential missing | Environment variable not set | List required env vars, suggest Secret Manager |
| Deployment quota exceeded | 429 or quota error | Suggest region change or quota increase request |

## Extension Points

- **Custom tools**: Add `.py` files to `src/tools/`, register in tool registry
- **New agent architectures**: ADK supports custom orchestration beyond Sequential/Parallel/Loop
- **Alternative deployment**: Local-only, Cloud Run, or custom infrastructure instead of Agent Engine
- **Testing expansion**: Add evaluation datasets, A/B prompt testing, latency benchmarks
