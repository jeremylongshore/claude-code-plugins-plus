# vercel-policy-guardrails

## Skill Scaffold

```
vercel-policy-guardrails/
  SKILL.md
```

## File Descriptions

### 1. SKILL.md
**Purpose:** Implement ESLint rules, pre-commit hooks, CI policy checks, OPA policies, and runtime guardrails.
**Workflow:** Set up during project initialization; enforced continuously through CI/CD.
**Relates to:** Follows vercel-reliability-patterns; leads to vercel-architecture-variants

## Summary

This skill covers automated policy enforcement for Vercel code. It includes custom ESLint plugin rules (no hardcoded keys, require error handling), pre-commit hooks for secrets detection, TypeScript strict patterns to prevent unsafe code, Architecture Decision Records template, Open Policy Agent (OPA) Rego policies for configuration validation, GitHub Actions CI policy workflow, and runtime guardrails for blocking dangerous operations in production. The goal is 100% policy compliance.
