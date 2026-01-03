# replit-known-pitfalls

## Skill Scaffold

```
replit-known-pitfalls/
  SKILL.md
```

## File Descriptions

### 1. SKILL.md
**Purpose:** Identify and avoid top 10 common Replit anti-patterns including resource leaks, public secrets, and port conflicts.
**Workflow:** Best practices skill - prevents common mistakes through awareness.
**Relates to:** Summarizes lessons from replit-common-errors; informs code review practices.

## Summary

This skill identifies and prevents common Replit anti-patterns. It covers avoiding hardcoded secrets in public Repls (use Secrets!), preventing memory leaks in long-running processes, handling port 0 vs explicit port binding correctly, understanding .replit vs replit.nix configuration precedence, avoiding excessive file writes that hit storage limits, managing package.json/requirements.txt version conflicts, preventing infinite loops that exhaust compute, understanding cold start behavior for Always On, avoiding synchronous blocking in async contexts, and handling database connection pooling properly. Learning from others' mistakes prevents your own.
