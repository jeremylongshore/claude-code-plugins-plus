---
name: speak-migration-deep-dive
description: |
  Execute Speak major re-architecture and migration strategies for language learning platforms.
  Use when migrating to or from Speak, performing major version upgrades,
  or re-platforming existing language learning integrations.
  Trigger with phrases like "migrate speak", "speak migration",
  "switch to speak", "speak replatform", "speak upgrade major".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*), Bash(kubectl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Speak Migration Deep Dive

## Current State
!`npm list 2>/dev/null | head -20`
!`pip freeze 2>/dev/null | head -20`

## Overview
Comprehensive guide for migrating to or from Speak, or major version upgrades for language learning platforms.

## Prerequisites
- Current system documentation
- Speak SDK installed
- Feature flag infrastructure
- Rollback strategy tested
- User communication plan

## Instructions
1. **Migration Types**
2. **Pre-Migration Assessment**
3. **Migration Strategy: Strangler Fig Pattern**
4. **Implementation Plan**
5. **Audio Migration**
6. **Rollback Plan**
7. **Post-Migration Validation**
8. **Post-Migration**

For full implementation details, load: `Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Migration assessment complete
- Adapter layer implemented
- User data migrated successfully
- Traffic fully shifted to Speak
- Rollback tested and documented

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Data mismatch | Transform errors | Validate transforms |
| Performance drop | No caching | Add caching layer |
| User confusion | UI changes | Provide tutorials |
| Audio format error | Incompatible format | Re-encode audio |

## Examples
### Quick Migration Status
```typescript
const status = await validateMigration();
console.log(`Migration ${status.passed ? 'PASSED' : 'FAILED'}`);
status.checks.forEach(c =>
  console.log(`  ${c.result.success ? 'OK' : 'FAIL'} ${c.name}`)
);
```

## Resources
- [Strangler Fig Pattern](https://martinfowler.com/bliki/StranglerFigApplication.html)
- [Speak Migration Guide](https://developer.speak.com/docs/migration)
- [Data Migration Best Practices](https://developer.speak.com/docs/data-migration)