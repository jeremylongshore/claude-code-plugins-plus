---
name: bmad-orchestrator
description: |
  Orchestrates BMAD workflows for structured AI-driven development.
  Use when initializing BMAD in a project, checking workflow status,
  or routing between development phases (Analysis, Planning, Solutioning, Implementation).
  Trigger with phrases like "workflow init", "workflow status", "bmad start", or "what phase am I in".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, TodoWrite
version: 6.2.2
author: BMad Code <bmadcode@bmad-method.org>
---

# BMAD Orchestrator

Central routing and workflow management for the BMAD method.

## Overview

The BMAD Orchestrator manages the 4-phase development lifecycle, routing users to the appropriate specialist agent and tracking project progress through artifact detection.

## Prerequisites

- `_bmad/` directory installed in project root
- `_bmad-output/` directory for artifact storage

## Instructions

1. Check `_bmad-output/` for existing artifacts to determine current phase
2. Assess project level (0-4) based on completed artifacts
3. Route to appropriate agent or workflow
4. Track progress and recommend next steps

### Phase Detection

- **Level 0**: No artifacts → recommend `/workflow-init`
- **Level 1**: Analysis complete → recommend `/create-prd`
- **Level 2**: PRD complete → recommend `/create-architecture`
- **Level 3**: Architecture complete → recommend `/plan-sprint`
- **Level 4**: Stories exist → recommend `/implement`

### Available Workflows

| Command | Phase | Description |
|---------|-------|-------------|
| `/workflow-init` | Setup | Initialize BMAD in project |
| `/workflow-status` | All | Check progress |
| `/analyze` | 1 | Business analysis |
| `/create-prd` | 2 | Product requirements |
| `/create-architecture` | 3 | System architecture |
| `/plan-sprint` | 4 | Sprint planning |
| `/implement` | 4 | Code implementation |
| `/code-review` | 4 | Code review |

## Output

- Project phase assessment
- Recommended next workflow
- Agent routing decisions

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| No `_bmad/` directory | BMAD not installed | Run installation |
| Missing prerequisites | Skipped a phase | Complete prior phase first |
| Conflicting artifacts | Manual edits | Review and reconcile |

## Examples

**Example: Check status**
Request: "What phase am I in?"
Result: Scans `_bmad-output/`, reports Level 2 (PRD complete), recommends architecture design

**Example: Initialize**
Request: "Start BMAD for my project"
Result: Creates project config, displays welcome, recommends starting with analysis

## Resources

- [BMAD Method Documentation](https://docs.bmad-method.org/)
- [Getting Started Guide](https://docs.bmad-method.org/tutorials/getting-started/)
