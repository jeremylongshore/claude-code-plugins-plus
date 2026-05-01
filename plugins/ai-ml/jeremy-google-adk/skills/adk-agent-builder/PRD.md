# PRD: ADK Agent Builder Skill

**Version:** 1.0.0
**Author:** Jeremy Longshore
**Date:** 2026-03-22
**Status:** Active
**Marketplace:** [tonsofskills.com](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io)
**Portfolio:** [jeremylongshore.com](https://jeremylongshore.com)

---

## Problem Statement

Building AI agents with Google's Agent Development Kit requires significant boilerplate: project structure, tool wiring, orchestration pattern selection, testing scaffolds, and deployment configuration. Developers waste hours on repeated setup tasks instead of focusing on agent logic. Without a structured approach, teams end up with inconsistent project layouts, missing tests, hardcoded credentials, and agents that work locally but fail in Vertex AI Agent Engine.

The ADK Agent Builder skill eliminates this friction by generating production-ready scaffolds tailored to the developer's use case, with correct patterns baked in from the start.

## Target Users

| User | Context | Primary Need |
|------|---------|-------------|
| GCP-native developers | Building agents on Vertex AI | Scaffold that matches ADK conventions and deploys cleanly to Agent Engine |
| AI/ML engineers | Prototyping multi-agent systems | Quick multi-agent orchestration setup with Sequential/Parallel/Loop patterns |
| Platform teams | Standardizing agent development | Repeatable, testable project structure with CI hooks |
| Solo developers | Shipping an agent for the first time | End-to-end guide from `pip install google-adk` to `adk deploy` |

## Success Criteria

1. **Time to first working agent**: Under 5 minutes from skill invocation to passing smoke test
2. **Deployment readiness**: Generated scaffold can deploy to Agent Engine without manual fixes
3. **Test coverage**: Every generated agent includes at least unit tests and one smoke prompt
4. **Zero hardcoded secrets**: All credentials flow through environment variables or Secret Manager
5. **Pattern accuracy**: Generated code uses correct ADK APIs (`google.adk.agents.Agent`, `google.adk.tools`, `google.adk.runners.Runner`)

## Functional Requirements

### FR-1: Scope Confirmation

Before generating anything, the skill confirms:
- Local-only agent vs. Vertex AI Agent Engine deployment
- Single-agent (ReAct) vs. multi-agent orchestration
- Tool surface (built-in ADK tools + custom tools)
- Required credentials and external service dependencies

### FR-2: Project Scaffolding

Generate a complete ADK project structure:

```
project-name/
  src/
    agents/
      __init__.py
      agent.py           # Main agent or orchestrator
    tools/
      __init__.py
      custom_tool.py     # Tool stubs with FunctionTool wrappers
  tests/
    test_agent.py        # Unit tests
    test_tools.py        # Tool-level tests
    smoke_prompts.txt    # Validation prompts for manual/CI testing
  pyproject.toml         # Dependencies with pinned google-adk version
  .env.example           # Required environment variables (no values)
  README.md              # Setup and run instructions
```

### FR-3: Agent Implementation

- **Single agent**: Uses `google.adk.agents.Agent` with `model`, `instruction`, and `tools` parameters. ReAct-style reasoning through ADK's built-in agent loop.
- **Multi-agent**: Uses `SequentialAgent`, `ParallelAgent`, or `LoopAgent` from `google.adk.agents` to compose specialist sub-agents.
- All agents include: name, description, instruction prompt, tool bindings, and model specification.

### FR-4: Tool Wiring

- Generate tool stubs using `google.adk.tools.FunctionTool` or `google.adk.tools.google_search`
- Each tool includes: docstring (used by the LLM for tool selection), typed parameters, return type, and error handling
- Tool registry pattern: tools declared in `src/tools/__init__.py` and imported by agent

### FR-5: Testing Scaffold

- Unit tests using `pytest` with mocked LLM responses
- Tool-level tests that validate input/output schemas
- Smoke prompts: plain-text prompts that exercise the agent end-to-end (for `adk run` or `Runner.run_async`)
- Integration test template for live API calls (skipped by default, enabled via env flag)

### FR-6: Deployment Support (Optional)

When deployment scope is confirmed:
- Generate `adk deploy cloud_run` or `adk deploy agent_engine` command
- Include post-deploy validation checklist:
  - Agent endpoint responds to health check
  - AgentCard accessible at `/.well-known/agent.json`
  - Task creation and streaming work via A2A protocol
  - IAM roles verified (Vertex AI User, Service Account Token Creator)
- Environment-specific configuration (staging vs. production)

### FR-7: Error Recovery Guidance

For every known failure mode, the skill provides:
- Specific error message or symptom
- Root cause
- Fix command or configuration change
- Regression test to prevent recurrence

## Non-Functional Requirements

### NFR-1: API Accuracy
All generated code must reference real ADK APIs. No fabricated class names or import paths. Core imports: `google.adk.agents`, `google.adk.tools`, `google.adk.runners`, `google.adk.sessions`.

### NFR-2: Security
- No credentials in generated files (use `.env.example` with empty values)
- Service account keys referenced via `GOOGLE_APPLICATION_CREDENTIALS` environment variable
- Recommend Workload Identity Federation over exported keys

### NFR-3: Portability
- Generated projects work on Python 3.10+ (ADK minimum requirement)
- No OS-specific dependencies
- Container-ready by default (Dockerfile optional but available)

### NFR-4: Idempotency
- Running the skill twice with the same inputs produces the same output
- Skill does not overwrite existing files unless explicitly confirmed

### NFR-5: Minimal Dependencies
- Core: `google-adk`, `google-cloud-aiplatform`, `pytest`
- No unnecessary framework dependencies (no LangChain, no CrewAI unless requested)

## Dependencies

| Dependency | Version | Purpose |
|-----------|---------|---------|
| `google-adk` | >= 1.0.0 | Core ADK framework |
| `google-cloud-aiplatform` | >= 1.74.0 | Vertex AI / Agent Engine deployment |
| `google-genai` | >= 1.0.0 | GenAI SDK (ADK's LLM backend) |
| Python | >= 3.10 | ADK minimum runtime |
| `pytest` | >= 7.0 | Testing framework |
| GCP project | Active, billing enabled | Required for Vertex AI features |

## Out of Scope

- **LangChain/CrewAI integration**: This skill is ADK-native. Use other skills for alternative frameworks.
- **Frontend/UI generation**: Agents are backend services. UI is a separate concern.
- **Custom model fine-tuning**: The skill uses existing Gemini/Claude models, not fine-tuned variants.
- **Multi-cloud deployment**: Targets GCP only (Vertex AI Agent Engine, Cloud Run).
- **Monitoring dashboard setup**: Generates logging/metrics hooks but not Grafana/Cloud Monitoring dashboards.
- **Data pipeline orchestration**: For Dataflow/Composer pipelines, use dedicated GCP skills.
