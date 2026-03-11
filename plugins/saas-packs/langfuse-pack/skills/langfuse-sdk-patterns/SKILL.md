---
name: langfuse-sdk-patterns
description: |
  Langfuse SDK best practices, patterns, and idiomatic usage.
  Use when learning Langfuse SDK patterns, implementing proper tracing,
  or following best practices for LLM observability.
  Trigger with phrases like "langfuse patterns", "langfuse best practices",
  "langfuse SDK guide", "how to use langfuse", "langfuse idioms".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Langfuse SDK Patterns

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Best practices and idiomatic patterns for using the Langfuse SDK, covering singleton clients, trace lifecycle, nested spans, decorators, sessions, and scoring.

## Prerequisites
- Completed `langfuse-install-auth` setup
- Understanding of async/await patterns
- Familiarity with LLM application structure

## Instructions

### Step 1: Use Singleton Client
Create a single Langfuse instance reused everywhere. Register `shutdownAsync()` for clean exit.

### Step 2: Manage Trace Lifecycle
Create trace at operation start. Update with output on success. Update with error level on failure. Never await flush in hot paths.

### Step 3: Nest Spans for Complex Operations
Use parent/child spans: validation span, retrieval span, generation for LLM calls. Always call `.end()`.

### Step 4: Use Python Decorators
Use `@observe()` for automatic span creation. Use `@observe(as_type="generation")` for LLM calls. Access context via `langfuse_context`.

### Step 5: Track Sessions and Users
Link traces across conversation turns using `sessionId`. Set `userId` for user-level analytics.

### Step 6: Add Evaluation Scores
Score traces with numeric values (0-1) for accuracy, relevance, and user feedback.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for advanced patterns.

## Output
- Singleton client pattern
- Proper trace lifecycle management
- Nested span hierarchy
- Python decorator-based tracing
- Session tracking and scoring

## Error Handling
| Pattern | Issue | Best Practice |
|---------|-------|---------------|
| Client creation | Multiple instances | Use singleton pattern |
| Trace updates | Missing outputs | Always update on success/error |
| Span nesting | Orphaned spans | Always call `.end()` in `finally` |
| Flush timing | Lost data | Use `shutdownAsync()` on exit |

## Examples


**Basic usage**: Apply langfuse sdk patterns to a standard project setup with default configuration options.

**Advanced scenario**: Customize langfuse sdk patterns for production environments with multiple constraints and team-specific requirements.

## Resources
- [Langfuse Tracing Guide](https://langfuse.com/docs/tracing)
- [Langfuse Python Decorators](https://langfuse.com/docs/sdk/python/decorators)
- [Langfuse Scores](https://langfuse.com/docs/scores)