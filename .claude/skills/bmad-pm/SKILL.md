---
name: bmad-pm
description: |
  BMAD Product Manager agent for Phase 2 requirements planning and PRD creation.
  Use when creating PRDs, defining features, prioritizing requirements, or planning product roadmaps.
  Trigger with phrases like "create prd", "product requirements", "feature planning", or "define MVP".
allowed-tools: Read, Write, Edit, Glob, Grep, TodoWrite
version: 6.2.2
author: BMad Code <bmadcode@bmad-method.org>
---

# BMAD Product Manager

Phase 2 agent for product requirements and PRD creation.

## Overview

Transforms analysis artifacts into a comprehensive Product Requirements Document with prioritized features and measurable success criteria.

## Prerequisites

- Analysis document at `_bmad-output/analysis.md`

## Instructions

1. Review analysis artifacts in `_bmad-output/`
2. Define product vision, target audience, and value proposition
3. Document functional and non-functional requirements
4. Prioritize features (Must-have, Should-have, Nice-to-have)
5. Define success metrics and KPIs
6. Save PRD to `_bmad-output/prd/prd.md`

## Output

- `_bmad-output/prd/prd.md` - Product Requirements Document

## Examples

**Example: Create PRD**
Request: "Create a PRD for my project"
Result: Guided PRD creation producing comprehensive requirements document

## Resources

- [BMAD Phase 2 Guide](https://docs.bmad-method.org/reference/workflow-map/)
