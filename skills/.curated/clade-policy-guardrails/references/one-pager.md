# clade-policy-guardrails — One-Pager

Implement content safety guardrails for Claude-powered applications with input filtering, output validation, and prompt injection defense.

## The Problem

Claude has strong built-in safety, but application-specific risks remain unaddressed without custom guardrails. Users can attempt prompt injection to override system instructions, outputs can accidentally leak system prompt content, and applications may inadvertently violate Anthropic's Acceptable Use Policy. Without defense-in-depth, a single successful injection can repurpose your Claude integration for unintended tasks.

## The Solution

This skill implements three layers of application-level guardrails: system prompt hardening with explicit behavioral rules, input validation that checks length limits and blocks common injection patterns (ignore instructions, DAN, etc.), and output validation that catches leaked system prompt content and enforces length limits. It complements Claude's built-in safety rather than duplicating it.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Developers building user-facing Claude applications that need application-specific content policies |
| **What** | Adds system prompt hardening, input validation with injection detection, and output validation with leak prevention |
| **When** | Before launching any Claude application that accepts untrusted user input |

## Key Features

1. **System Prompt Hardening** — Template with explicit behavioral rules, scope boundaries, and fallback instructions to resist prompt injection
2. **Input Validation with Injection Detection** — Validates message length and regex-scans for common injection patterns (ignore instructions, role overrides, DAN)
3. **Output Validation** — Catches accidental system prompt leaks by scanning for rule markers and enforces response length limits

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
