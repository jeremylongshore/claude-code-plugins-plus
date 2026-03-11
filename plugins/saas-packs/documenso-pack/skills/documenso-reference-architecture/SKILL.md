---
name: documenso-reference-architecture
description: |
  Implement Documenso reference architecture with best-practice project layout.
  Use when designing new Documenso integrations, reviewing project structure,
  or establishing architecture standards for document signing applications.
  Trigger with phrases like "documenso architecture", "documenso best practices",
  "documenso project structure", "how to organize documenso".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Documenso Reference Architecture

## Overview
Production-ready architecture patterns for Documenso document signing integrations.

## Prerequisites
- Understanding of layered architecture
- Documenso SDK knowledge
- TypeScript project setup
- Testing framework configured

## Instructions

### Step 1: Project Structure
my-signing-app/
### Step 2: Layer Architecture
┌─────────────────────────────────────────┐
### Step 3: Key Components
// src/documenso/client.ts
### Step 4: Data Flow Diagram
User Request
### Step 5: Webhook Architecture
Documenso
### Step 6: Setup Script
mkdir -p src/documenso/handlers

For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Project Structure
- Layer Architecture
- Key Components
- Data Flow Diagram
- Webhook Architecture
- Setup Script

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Circular dependencies | Wrong layering | Separate by layer |
| Config not loading | Wrong paths | Verify file locations |
| Cache misses | Wrong keys | Check key generation |
| Test isolation | Shared state | Use dependency injection |

## Resources
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Documenso SDK](https://github.com/documenso/sdk-typescript)
- [TypeScript Project References](https://www.typescriptlang.org/docs/handbook/project-references.html)

## Next Steps
For multi-environment setup, see `documenso-multi-env-setup`.

## Examples

**Basic usage**: Apply documenso reference architecture to a standard project setup with default configuration options.

**Advanced scenario**: Customize documenso reference architecture for production environments with multiple constraints and team-specific requirements.