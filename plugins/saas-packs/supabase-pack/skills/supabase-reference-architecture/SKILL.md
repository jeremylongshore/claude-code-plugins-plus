---
name: supabase-reference-architecture
description: |
  Implement Supabase reference architecture with best-practice project layout.
  Use when designing new Supabase integrations, reviewing project structure,
  or establishing architecture standards for Supabase applications.
  Trigger with phrases like "supabase architecture", "supabase best practices",
  "supabase project structure", "how to organize supabase", "supabase layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Supabase Reference Architecture

## Prerequisites
- Understanding of layered architecture
- Supabase SDK knowledge
- TypeScript project setup
- Testing framework configured

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Supabase operations.

### Step 4: Configure Health Checks
Add health check endpoint for Supabase connectivity.

## Output
- Structured project layout
- Client wrapper with caching
- Error boundary implemented
- Health checks configured

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources
- [Supabase SDK Documentation](https://supabase.com/docs/sdk)
- [Supabase Best Practices](https://supabase.com/docs/best-practices)
