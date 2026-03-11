---
name: lokalise-reference-architecture
description: |
  Implement Lokalise reference architecture with best-practice project layout.
  Use when designing new Lokalise integrations, reviewing project structure,
  or establishing architecture standards for Lokalise applications.
  Trigger with phrases like "lokalise architecture", "lokalise best practices",
  "lokalise project structure", "how to organize lokalise", "lokalise layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Lokalise Reference Architecture

## Overview
Production-ready architecture patterns for Lokalise integrations.

## Prerequisites
- Understanding of layered architecture
- Lokalise SDK knowledge
- TypeScript project setup
- Testing framework configured

## Instructions
1. **Project Structure**
2. **Layer Architecture**
3. **Key Components**
4. **Data Flow Diagram**
5. **Configuration Management**
6. **Instructions**
7. **Flagship Skills**

For full implementation details, load: `Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Structured project layout
- Client wrapper with caching
- Translation service facade
- i18n library integration

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Circular imports | Wrong layering | Separate by layer |
| Missing locale | Not bundled | Add fallback logic |
| Stale translations | Cache not invalidated | Use webhooks to invalidate |
| Type errors | Missing types | Generate from source locale |

## Examples
See `references/implementation-guide.md` for detailed examples.

## Resources
- [Lokalise SDK Documentation](https://lokalise.github.io/node-lokalise-api/)
- [i18next Documentation](https://www.i18next.com/)
- [React i18next](https://react.i18next.com/)