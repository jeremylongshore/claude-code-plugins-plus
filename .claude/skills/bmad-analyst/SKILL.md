---
name: bmad-analyst
description: |
  BMAD Business Analyst agent for Phase 1 discovery and requirements analysis.
  Use when conducting business analysis, stakeholder mapping, or requirements gathering.
  Trigger with phrases like "analyze project", "business analysis", "discovery", or "gather requirements".
allowed-tools: Read, Write, Edit, Glob, Grep, TodoWrite
version: 6.2.2
author: BMad Code <bmadcode@bmad-method.org>
---

# BMAD Business Analyst

Phase 1 agent for business discovery and requirements analysis.

## Overview

Guides structured business analysis to understand the problem space, identify stakeholders, and document requirements before technical decisions are made.

## Prerequisites

- `_bmad/` directory installed
- `_bmad-output/` directory available for artifact storage

## Instructions

1. Conduct project discovery (business problem, target users, goals)
2. Map stakeholders and their priorities
3. Gather functional and non-functional requirements
4. Identify constraints and assumptions
5. Document findings in `_bmad-output/analysis.md`

## Output

- `_bmad-output/analysis.md` - Comprehensive analysis document

## Examples

**Example: Start analysis**
Request: "Analyze my project requirements"
Result: Guided discovery session producing analysis document

## Resources

- [BMAD Phase 1 Guide](https://docs.bmad-method.org/reference/workflow-map/)
