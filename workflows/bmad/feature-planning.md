# Feature Planning Workflow

> BMAD-compatible workflow for planning Claude Code plugin features

## Overview

This workflow guides you through planning a new plugin feature using BMAD's agent-role methodology. Uses Analyst, PM, and Architect agents to create detailed specifications.

## Prerequisites

- Clear feature idea or user request
- Access to existing plugin codebase
- Understanding of Claude Code plugin architecture

## Phase 1: Analysis (Analyst Agent)

### 1.1 Context Gathering

```
As the Analyst agent, gather context:

1. What problem does this feature solve?
2. Who are the target users?
3. What existing solutions exist?
4. What constraints apply (technical, time, resources)?
```

### 1.2 Research Questions

- [ ] What similar features exist in other plugins?
- [ ] What dependencies will this require?
- [ ] Are there security implications?
- [ ] How does this fit with existing functionality?

### 1.3 Analysis Output

Create `analysis.md` with:
- Problem statement
- User personas
- Competitive analysis
- Initial feasibility assessment

---

## Phase 2: Planning (PM Agent)

### 2.1 Requirements Definition

```
As the PM agent, define requirements:

1. Functional requirements (what it must do)
2. Non-functional requirements (performance, security)
3. User stories with acceptance criteria
4. Success metrics
```

### 2.2 PRD Template

```markdown
# Product Requirements Document

## Feature: [Feature Name]

### Problem Statement
[From Analysis phase]

### Goals
- Primary:
- Secondary:

### User Stories
1. As a [user type], I want [goal] so that [benefit]
   - Acceptance: [criteria]

### Requirements
#### Functional
- FR1:
- FR2:

#### Non-Functional
- NFR1: Performance -
- NFR2: Security -

### Success Metrics
- Metric 1:
- Metric 2:

### Out of Scope
- Item 1:
```

### 2.3 Prioritization

Use MoSCoW method:
- **Must Have**: Core functionality
- **Should Have**: Important but not critical
- **Could Have**: Nice to have
- **Won't Have**: Explicitly excluded

---

## Phase 3: Solutioning (Architect Agent)

### 3.1 Architecture Design

```
As the Architect agent, design the solution:

1. Component structure
2. Data flow
3. Integration points
4. Technology choices
```

### 3.2 Technical Specification Template

```markdown
# Technical Specification

## Architecture Overview
[Diagram or description]

## Components
### Component 1: [Name]
- Purpose:
- Inputs:
- Outputs:
- Dependencies:

## Data Model
[Schema or structure]

## API Design
[Endpoints or interfaces]

## Integration Points
- Claude Code hooks:
- MCP servers:
- External APIs:

## Security Considerations
- Authentication:
- Authorization:
- Data handling:

## Testing Strategy
- Unit tests:
- Integration tests:
- E2E tests:
```

### 3.3 Architecture Review Checklist

- [ ] Follows Claude Code plugin conventions
- [ ] Minimal dependencies
- [ ] Security best practices
- [ ] Error handling defined
- [ ] Logging strategy
- [ ] Documentation plan

---

## Outputs

After completing this workflow, you should have:

1. **analysis.md** - Problem analysis and research
2. **prd.md** - Product requirements document
3. **tech-spec.md** - Technical specification
4. **stories/** - Directory with user stories

## Next Steps

1. Review outputs with stakeholders
2. Proceed to implementation with Developer agent
3. Or iterate on planning if gaps identified

## Integration with MCP Servers

Use these MCP servers during planning:

| Server | Use Case |
|--------|----------|
| project-health-auditor | Assess existing codebase |
| domain-memory-agent | Store planning context |
| workflow-orchestrator | Track planning phases |

---

*Part of Claude Code Plugins Marketplace - https://claudecodeplugins.io/*
