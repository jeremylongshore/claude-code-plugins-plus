# PRD: ADK Engineer

**Version:** 2.1.0
**Author:** Jeremy Longshore
**Status:** Active
**Marketplace:** [tonsofskills.com](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io)
**Portfolio:** [jeremylongshore.com](https://jeremylongshore.com)

---

## Problem Statement

ADK agent code that works in a prototype rarely survives production. Missing test coverage, inconsistent module boundaries, hardcoded tool configurations, and ad-hoc deployment scripts create agents that break on first contact with real traffic. Refactoring after the fact costs 3-5x more than building correctly upfront.

The ADK Engineer skill produces production-grade agent code with clean architecture, test coverage, and deployment automation from the start.

## Target Users

| User | Context | Primary Need |
|------|---------|-------------|
| ADK developers | Building new agents | Clean structure with tests from day one |
| Teams with existing agents | Refactoring for production | Module boundaries, test coverage, deployment plan |
| Platform engineers | Standardizing agent development | Repeatable patterns across teams |
| Solo developers | Shipping agent products | End-to-end from code to deployed, tested agent |

## Success Criteria

1. **Code structure**: Generated code follows single-responsibility modules with clear interfaces
2. **Test coverage**: Every tool function has unit tests; every agent has smoke prompt tests
3. **Incremental builds**: Each tool added independently with its own validation before wiring to agent
4. **Deployment readiness**: Generated code deploys without manual intervention to the target platform
5. **Operational safety**: Retries, timeouts, structured logging, and safe error messages built in

## Functional Requirements

1. Clarify agent requirements (goals, tools, constraints, deployment target)
2. Propose architecture (single vs multi-agent, orchestration, state management)
3. Scaffold project structure with proper module boundaries
4. Implement tools incrementally — one at a time, each with tests
5. Add operational guardrails (retries, backoff, timeouts, logging)
6. Validate locally (unit tests + smoke prompts)
7. Generate deployment plan with health checks

## Non-Functional Requirements

- Supports Python, Java, and Go runtimes
- Works with any ADK-compatible model provider
- Generates CI-compatible test commands
- Code follows language-specific conventions (PEP 8 for Python, etc.)

## Dependencies

- Target language runtime installed
- ADK SDK installed and configured
- Test runner available (pytest, JUnit, go test)
- GCP project access for deployment (optional)

## Out of Scope

- Model fine-tuning or training
- UI/frontend development
- Infrastructure provisioning (use jeremy-adk-terraform for that)
- Production monitoring setup (use jeremy-vertex-validator)
