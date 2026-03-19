---
name: documenso-migration-deep-dive
description: |
  Execute comprehensive Documenso migration strategies for platform switches.
  Use when migrating from other signing platforms, re-platforming to Documenso,
  or performing major infrastructure changes.
  Trigger with phrases like "migrate to documenso", "documenso migration",
  "switch to documenso", "documenso replatform", "replace docusign".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Documenso Migration Deep Dive

## Current State
!`npm list 2>/dev/null | head -20`
!`pip freeze 2>/dev/null | head -20`

## Overview
Comprehensive guide for migrating to Documenso from other e-signature platforms or implementing major architectural changes.

## Prerequisites
- Current system documentation
- Documenso account configured
- Feature flag infrastructure
- Rollback strategy tested

## Instructions

### Step 1: Migration Types
Implement migration types.
### Step 2: Migration Strategy: Strangler Fig Pattern
Phase 1: Parallel Systems
### Step 3: Pre-Migration Assessment
// scripts/analyze-current-system.ts
### Step 4: Implementation Plan
// Step 1: Install Documenso SDK alongside existing
### Step 5: Rollback Procedure
echo "Rolling back Documenso migration..."
### Step 6: Congratulations!
You have completed the Documenso Skill Pack. Review other skills as needed for ongoing operations.

For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Migration Types
- Migration Strategy: Strangler Fig Pattern
- Pre-Migration Assessment
- Implementation Plan
- Rollback Procedure
- Congratulations!

## Error Handling
| Migration Issue | Cause | Solution |
|----------------|-------|----------|
| Field mapping failed | Different coordinates | Adjust position calculation |
| Webhook format | Different payload | Normalize events |
| Template missing | Not recreated | Create in Documenso |
| High error rate | Integration bug | Pause rollout, investigate |

## Resources
- [Strangler Fig Pattern](https://martinfowler.com/bliki/StranglerFigApplication.html)
- [Feature Flags](https://launchdarkly.com/blog/feature-flags-best-practices/)
- [Documenso Documentation](https://docs.documenso.com)

## Next Steps
Review related skills for comprehensive coverage.

## Examples

**Basic usage**: Apply documenso migration deep dive to a standard project setup with default configuration options.

**Advanced scenario**: Customize documenso migration deep dive for production environments with multiple constraints and team-specific requirements.