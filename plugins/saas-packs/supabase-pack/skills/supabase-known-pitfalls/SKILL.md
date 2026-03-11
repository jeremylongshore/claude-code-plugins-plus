---
name: supabase-known-pitfalls
description: |
  Execute identify and avoid Supabase anti-patterns and common integration mistakes.
  Use when reviewing Supabase code for issues, onboarding new developers,
  or auditing existing Supabase integrations for best practices violations.
  Trigger with phrases like "supabase mistakes", "supabase anti-patterns",
  "supabase pitfalls", "supabase what not to do", "supabase code review".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Supabase Known Pitfalls

## Prerequisites
- Access to Supabase codebase for review
- Understanding of async/await patterns
- Knowledge of security best practices
- Familiarity with rate limiting concepts

## Instructions

### Step 1: Review for Anti-Patterns
Scan codebase for each pitfall pattern.

### Step 2: Prioritize Fixes
Address security issues first, then performance.

### Step 3: Implement Better Approach
Replace anti-patterns with recommended patterns.

### Step 4: Add Prevention
Set up linting and CI checks to prevent recurrence.

## Output
- Anti-patterns identified
- Fixes prioritized and implemented
- Prevention measures in place
- Code quality improved

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources
- [Supabase Security Guide](https://supabase.com/docs/security)
- [Supabase Best Practices](https://supabase.com/docs/best-practices)
