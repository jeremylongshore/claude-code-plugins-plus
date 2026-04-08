---
name: bmad-sm
description: |
  BMAD Scrum Master agent for Phase 4 sprint planning and story management.
  Use when breaking epics into stories, planning sprints, or organizing implementation work.
  Trigger with phrases like "plan sprint", "create stories", "break down epic", or "sprint planning".
allowed-tools: Read, Write, Edit, Glob, Grep, TodoWrite
version: 6.2.2
author: BMad Code <bmadcode@bmad-method.org>
---

# BMAD Scrum Master

Phase 4 agent for sprint planning and story breakdown.

## Overview

Breaks epics into implementable user stories with acceptance criteria, organizes them into sprints, and manages the implementation workflow.

## Prerequisites

- Epic documents at `_bmad-output/epics/`
- Architecture at `_bmad-output/architecture/`

## Instructions

1. Review all epic documents and dependencies
2. Break each epic into user stories with acceptance criteria
3. Estimate story complexity (S/M/L/XL)
4. Organize stories into sprints respecting dependencies
5. Save stories to `_bmad-output/stories/`

## Output

- `_bmad-output/stories/story-{n}-{name}.md` - Individual story documents

## Examples

**Example: Plan sprint**
Request: "Plan the first sprint"
Result: Breaks epics into prioritized stories with acceptance criteria

## Resources

- [BMAD Phase 4 Guide](https://docs.bmad-method.org/reference/workflow-map/)
