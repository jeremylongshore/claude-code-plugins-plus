---
name: lindy-migration-deep-dive
description: |
  Advanced migration strategies for Lindy AI integrations.
  Use when migrating from other platforms, consolidating agents,
  or performing major architecture changes.
  Trigger with phrases like "lindy migration", "migrate to lindy",
  "lindy platform migration", "switch to lindy".
allowed-tools: Read, Write, Edit, Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Lindy Migration Deep Dive

## Current State
!`npm list 2>/dev/null | head -20`
!`pip freeze 2>/dev/null | head -20`

## Overview
Advanced migration strategies for moving to or upgrading Lindy AI integrations including platform migration, agent consolidation, and multi-environment rollout.

## Prerequisites
- Source platform documentation
- Target Lindy environment ready
- Migration timeline approved
- Rollback plan defined

## Instructions

### Step 1: Assess Migration Scope
Analyze source system agents and workflows. Classify complexity (simple/moderate/complex) and estimate duration based on agent count and workflow complexity.

### Step 2: Plan Agent Consolidation
Identify duplicate or overlapping agents. Merge instructions, collect unique tools, and create consolidated agents with clear specialization sections.

### Step 3: Create Multi-Environment Migration Plan
Define phases (development, staging, production) with specific steps, duration, and success criteria for each. Include rollback checkpoints at key milestones.

### Step 4: Execute Data Migration
Export from source, transform to Lindy format using source-specific transforms (OpenAI, LangChain, custom), validate, and import.

### Step 5: Set Up Rollback Procedures
Create checkpoint snapshots of agents and automations before each phase. Implement rollback that deletes new agents and restores modified ones.

### Step 6: Run Migration Script
Execute the phased migration: assess, export, transform, validate, checkpoint, import, test.

For detailed implementation code and migration scripts, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Migration Checklist
- [ ] Source system documented
- [ ] Migration plan approved
- [ ] Rollback procedures tested
- [ ] Data transformation validated
- [ ] Feature parity confirmed
- [ ] Integration tests created
- [ ] Load tests passed
- [ ] Parallel run completed
- [ ] Cutover window scheduled
- [ ] Support team briefed

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Data loss | Transform error | Validate before import |
| Parity gap | Feature difference | Document and workaround |
| Rollback fail | Incomplete checkpoint | Create full snapshots |

## Resources
- [Lindy Migration Guide](https://docs.lindy.ai/migration)
- [Data Import API](https://docs.lindy.ai/api/import)
- [Best Practices](https://docs.lindy.ai/migration/best-practices)

## Next Steps
This completes the Flagship tier skills. Consider reviewing Standard and Pro skills for comprehensive coverage.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

See [migration implementation details](${CLAUDE_SKILL_DIR}/references/implementation.md) for output format specifications.

## Examples

**Basic usage**: Apply lindy migration deep dive to a standard project setup with default configuration options.

**Advanced scenario**: Customize lindy migration deep dive for production environments with multiple constraints and team-specific requirements.