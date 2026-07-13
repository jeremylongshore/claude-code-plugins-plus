# clade-advanced-troubleshooting — One-Pager

Debug the hard Claude API problems that basic error handling won't catch.

## The Problem

Once you get past authentication and rate limits, Claude integrations surface subtler issues: inconsistent outputs across identical prompts, tool use calls to nonexistent functions, streaming connections that drop without a `message_stop` event, responses that truncate mid-sentence, and images Claude claims it cannot see. These problems are intermittent, hard to reproduce, and not covered by standard error codes.

## The Solution

This skill provides production-ready detection and fix patterns for each failure mode. It covers temperature control for deterministic outputs, tool name validation before execution, stream completeness checks, `stop_reason` inspection for truncation, and correct base64 image formatting. Each pattern includes copy-paste TypeScript code.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Developers maintaining Claude API integrations in production |
| **What** | Diagnose and fix inconsistent outputs, tool use failures, streaming drops, truncation, and vision format issues |
| **When** | After basic error handling is in place (see `clade-common-errors`) and you hit edge-case failures |

## Key Features

1. **Temperature control** — Set `temperature: 0` to eliminate randomness when deterministic output is required
2. **Tool use validation** — Check `toolUse.name` against your defined tool list before executing, and return structured errors for unknown tools
3. **Stream completeness detection** — Track `message_stop` events to detect and retry dropped connections
4. **Truncation awareness** — Inspect `stop_reason === 'max_tokens'` to catch mid-sentence cutoffs before they reach users
5. **Image format fixes** — Correct media_type, raw base64 (no data URI prefix), 5MB limit, and supported format checklist

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
