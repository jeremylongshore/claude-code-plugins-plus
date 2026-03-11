---
name: customerio-sdk-patterns
description: |
  Apply production-ready Customer.io SDK patterns.
  Use when implementing best practices, refactoring integrations,
  or optimizing Customer.io usage in your application.
  Trigger with phrases like "customer.io best practices", "customer.io patterns",
  "production customer.io", "customer.io architecture".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Customer.io SDK Patterns

## Overview
Production-ready patterns for Customer.io SDK usage including type-safe clients, retry logic, event batching, and singleton management.

## Prerequisites
- Customer.io SDK installed
- TypeScript project (recommended)
- Understanding of async/await patterns

## Instructions

### Step 1: Build a Type-Safe Client
Define TypeScript interfaces for user attributes and event names. Create a typed wrapper that enforces correct attribute types and event name enums.

### Step 2: Add Retry with Exponential Backoff
Wrap operations with configurable retry logic that handles transient errors with exponential delay and skips retries on client errors.

### Step 3: Implement Event Queue with Batching
Build an event queue that buffers track calls, auto-flushes on size threshold or time interval, and processes in parallel batches.

### Step 4: Use Singleton with Lazy Initialization
Create a singleton factory that validates credentials and reuses a single TrackClient instance across the application.

For detailed implementation code and patterns, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Type-safe Customer.io client with TypeScript interfaces
- Resilient error handling with configurable retries
- Event batching for high-volume scenarios
- Singleton pattern for resource efficiency

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Type mismatch | Invalid attribute type | Use TypeScript interfaces |
| Queue overflow | Too many events | Increase flush frequency |
| Retry exhausted | Persistent failure | Check network and credentials |

## Resources
- [Customer.io SDK GitHub](https://github.com/customerio/customerio-node)
- [API Rate Limits](https://customer.io/docs/api/track/#section/Limits)

## Next Steps
After implementing patterns, proceed to `customerio-primary-workflow` for messaging workflows.

## Examples

**Basic usage**: Apply customerio sdk patterns to a standard project setup with default configuration options.

**Advanced scenario**: Customize customerio sdk patterns for production environments with multiple constraints and team-specific requirements.