---
name: supabase-policy-guardrails
description: |
  Implement Supabase lint rules, policy enforcement, and automated guardrails.
  Use when setting up code quality rules for Supabase integrations, implementing
  pre-commit hooks, or configuring CI policy checks for Supabase best practices.
  Trigger with phrases like "supabase policy", "supabase lint",
  "supabase guardrails", "supabase best practices check", "supabase eslint".
allowed-tools: Read, Write, Edit, Bash(npx:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Supabase Policy Guardrails

## Prerequisites
- ESLint configured in project
- Pre-commit hooks infrastructure
- CI/CD pipeline with policy checks
- TypeScript for type enforcement

## Instructions

### Step 1: Create ESLint Rules
Implement custom lint rules for Supabase patterns.

### Step 2: Configure Pre-Commit Hooks
Set up hooks to catch issues before commit.

### Step 3: Add CI Policy Checks
Implement policy-as-code in CI pipeline.

### Step 4: Enable Runtime Guardrails
Add production safeguards for dangerous operations.

## Output
- ESLint plugin with Supabase rules
- Pre-commit hooks blocking secrets
- CI policy checks passing
- Runtime guardrails active

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources
- [ESLint Plugin Development](https://eslint.org/docs/latest/extend/plugins)
- [Pre-commit Framework](https://pre-commit.com/)
- [Open Policy Agent](https://www.openpolicyagent.org/)
