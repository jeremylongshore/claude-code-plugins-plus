---
name: obsidian-reference-architecture
description: |
  Implement Obsidian reference architecture with best-practice project layout.
  Use when designing new plugins, reviewing project structure,
  or establishing architecture standards for Obsidian development.
  Trigger with phrases like "obsidian architecture", "obsidian project structure",
  "obsidian best practices", "organize obsidian plugin".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Obsidian Reference Architecture

## Overview
Production-ready architecture patterns for Obsidian plugin development.

## Prerequisites
- Understanding of layered architecture
- TypeScript and Obsidian API knowledge
- Project setup complete

## Instructions

See implementation guide for detailed steps.

For full implementation details and code examples, load:
`references/implementation-guide.md`

## Output
- Organized project structure
- Clear separation of concerns
- Reusable service layer
- Centralized event management
- Type-safe settings

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Circular dependencies | Wrong imports | Use interface segregation |
| Missing types | Incomplete definitions | Create types.ts |
| Event leaks | Unregistered events | Use registerEvent |
| Settings lost | Migration missing | Implement version migration |

## Resources
- [Obsidian Plugin Guidelines](https://docs.obsidian.md/Plugins/Releasing/Plugin+guidelines)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
