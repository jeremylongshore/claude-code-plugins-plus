# BMAD Workflow Map

## Phase Flow

```
Phase 1: Analysis          Phase 2: Planning
┌─────────────────┐       ┌─────────────────┐
│   Analyst Agent  │──────▶│    PM Agent      │
│                  │       │                  │
│ - Discovery      │       │ - PRD Creation   │
│ - Requirements   │       │ - Prioritization │
│ - Stakeholders   │       │ - Metrics        │
└─────────────────┘       └────────┬─────────┘
                                   │
                                   ▼
Phase 4: Implementation   Phase 3: Solutioning
┌─────────────────┐       ┌─────────────────┐
│  Dev/SM/QA       │◀──────│ Architect Agent  │
│                  │       │                  │
│ - Sprint Plan    │       │ - Architecture   │
│ - Implementation │       │ - Tech Stack     │
│ - Code Review    │       │ - Epic Breakdown │
│ - Testing        │       │ - System Design  │
└─────────────────┘       └─────────────────┘
```

## Cross-Phase Agents

- **UX Designer**: Available across all phases for UX guidance
- **BMAD Orchestrator**: Routes between phases and tracks progress
- **BMAD Help**: Provides guidance at any point

## Artifact Flow

```
Analysis Docs → PRD → Architecture Docs → Epics → Stories → Code
```

Each phase produces artifacts in `_bmad-output/` that feed into the next phase.
