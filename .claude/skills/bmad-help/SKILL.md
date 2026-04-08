---
name: bmad-help
description: |
  Provides guidance on using the BMAD method, explains available workflows and agents,
  and helps determine next steps based on project state.
  Use when asking "what should I do next", "bmad help", or "how does BMAD work".
  Trigger with phrases like "bmad help", "bmad guide", "what's next", or "how do I use bmad".
allowed-tools: Read, Glob, Grep
version: 6.2.2
author: BMad Code <bmadcode@bmad-method.org>
---

# BMAD Help

Guidance and navigation for the BMAD method.

## Overview

Helps users understand the BMAD method, discover available workflows and agents, and determine their next steps based on current project state.

## Prerequisites

- `_bmad/` directory present in project

## Instructions

1. Read `_bmad/_config/manifest.yaml` to identify installed modules
2. Read `_bmad/_config/bmad-help.csv` for available topics
3. Scan `_bmad-output/` to assess current project phase
4. Provide contextual guidance based on project state

### BMAD Overview

BMAD uses 4 phases with specialized agents:
1. **Analysis** (Analyst) - Understand the problem
2. **Planning** (PM) - Define requirements
3. **Solutioning** (Architect) - Design architecture
4. **Implementation** (Dev/SM/QA) - Build and test

### Quick Start

- New project? Say "Initialize BMAD"
- Already started? Say "What should I do next?"
- Need help with a phase? Say "Help with [phase name]"

## Output

- Current project state assessment
- Available commands and agents
- Contextual next-step recommendations

## Examples

**Example: Getting started**
Request: "bmad help"
Result: Shows overview of BMAD method, available commands, and recommended first step

**Example: Next steps**
Request: "I just finished the architecture, what do I do next?"
Result: Recommends sprint planning with the Scrum Master agent

## Resources

- [BMAD Method Documentation](https://docs.bmad-method.org/)
