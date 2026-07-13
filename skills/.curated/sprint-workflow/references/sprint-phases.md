# Sprint Phases

## Sprint Phases

A sprint executes through 6 distinct phases:

### Phase 0: Load Specifications

Parse the sprint directory and prepare context:

- Locate sprint directory (`.claude/sprint/[N]/`)
- Read `specs.md` for user requirements
- Read `status.md` if resuming
- Detect project type for framework-specific agents

### Phase 1: Architectural Planning

The project-architect agent analyzes requirements:

- Read existing `project-map.md` for architecture context
- Read `project-goals.md` for business objectives
- Create specification files (`api-contract.md`, `backend-specs.md`, etc.)
- Return SPAWN REQUEST for implementation agents

### Phase 2: Implementation

Spawn implementation agents in parallel:

- `python-dev` for Python/FastAPI backend
- `nextjs-dev` for Next.js frontend
- `cicd-agent` for CI/CD pipelines
- `allpurpose-agent` for any other technology
- Collect structured reports from each agent

### Phase 3: Testing

Execute testing agents:

- `qa-test-agent` runs first (API and unit tests)
- `ui-test-agent` runs after (browser-based E2E tests)
- Framework-specific diagnostics agents run in parallel with UI tests
- Collect test reports

### Phase 4: Review & Iteration

Architect reviews all reports:

- Analyze conformity status
- Update specifications (remove completed, add fixes)
- Update `status.md` with current state
- Decide: more implementation, more testing, or finalize

### Phase 5: Finalization

Sprint completion:

- Final `status.md` summary
- All specs in consistent state
- **Clean up manual-test-report.md** (no longer relevant)
- Signal FINALIZE to orchestrator
