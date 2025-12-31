# retellai-known-pitfalls

> Identify and avoid 10 common anti-patterns including blocking calls, poor error handling, and voice misuse

## Directory Structure

```
retellai-known-pitfalls/
├── SKILL.md
└── examples/
    └── example.py
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| SKILL.md | Markdown | Core skill instructions for avoiding common anti-patterns |
| examples/example.py | Python | Example good patterns vs anti-patterns comparison |

## Summary

**Category:** advanced
**Target Audience:** All Retell AI developers, Code reviewers, Tech leads
**Trigger Phrases:** `retell mistakes`, `retell anti-patterns`, `retell pitfalls`, `retell what not to do`

### What This Skill Does

This skill identifies and helps developers avoid the 10 most common Retell AI anti-patterns. It covers blocking API calls in voice handlers (causing latency), ignoring error responses, hardcoding API keys, mismatched voice/persona, overly complex conversation flows, missing webhook signature verification, ignoring rate limits, synchronous transcript processing, missing health checks, and poor logging practices.

### Technical Success Criteria

- Anti-patterns identified in existing code
- Fixes prioritized by impact
- Prevention measures in place (linting, code review)
- Team educated on common pitfalls

### Business Success Criteria

- Reduced production incidents from known issues
- Improved code quality across team
- Eliminate 100% of common pitfalls in new code

## Related Skills

- retellai-reference-architecture - Correct patterns to follow
- retellai-security-basics - Security-related pitfalls
- retellai-common-errors - Error resolution
