---
name: vercel-reference-architecture
description: |
  Implement Vercel reference architecture with best-practice project layout.
  Use when designing new Vercel integrations, reviewing project structure,
  or establishing architecture standards for Vercel applications.
  Trigger with phrases like "vercel architecture", "vercel best practices",
  "vercel project structure", "how to organize vercel", "vercel layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Vercel Reference Architecture

## Prerequisites
- Understanding of layered architecture
- Vercel SDK knowledge
- TypeScript project setup
- Testing framework configured

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Vercel operations.

### Step 4: Configure Health Checks
Add health check endpoint for Vercel connectivity.

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
- [Vercel SDK Documentation](https://vercel.com/docs/sdk)
- [Vercel Best Practices](https://vercel.com/docs/best-practices)

## Overview

Implement Vercel reference architecture with best-practice project layout.