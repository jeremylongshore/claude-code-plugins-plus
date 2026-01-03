# vercel-debug-bundle

## Skill Scaffold

```
vercel-debug-bundle/
  SKILL.md
```

## File Descriptions

### 1. SKILL.md
**Purpose:** Collect comprehensive diagnostic information for Vercel support tickets including environment info, redacted logs, and network tests.
**Workflow:** Used when preparing support tickets or investigating persistent issues requiring external help.
**Relates to:** Escalation path from vercel-common-errors; provides evidence for vercel-incident-runbook postmortems

## Summary

This skill automates the collection of all diagnostic information needed for effective Vercel support tickets. It creates a structured debug bundle containing environment versions, SDK versions, redacted logs (with secrets removed), configuration files (sanitized), and network connectivity tests. The bundle is packaged for easy upload to support portals while ensuring sensitive data is never exposed.
