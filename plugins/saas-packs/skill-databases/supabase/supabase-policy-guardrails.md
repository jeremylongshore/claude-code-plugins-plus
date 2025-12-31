# supabase-policy-guardrails

## File Scaffold

```
supabase-policy-guardrails/
-- SKILL.md
```

## File Descriptions

### 1. SKILL.md
**Purpose:** Implement Supabase lint rules, policy enforcement with ESLint and OPA, pre-commit hooks, CI policy checks, and runtime guardrails.
**Workflow:** Policy enforcement skill. Used for automated code quality and security enforcement.
**Relates to:** Builds on supabase-reliability-patterns; enforces patterns from supabase-sdk-patterns.

## Summary

This skill provides automated policy enforcement for Supabase integrations. It covers custom ESLint plugin rules for detecting hardcoded keys, pre-commit hooks for secrets detection, TypeScript strict patterns, Architecture Decision Records, Open Policy Agent (OPA) policy-as-code, CI policy checks with GitHub Actions, and runtime guardrails for production protection. Use this skill when establishing code quality rules or implementing automated security checks.
