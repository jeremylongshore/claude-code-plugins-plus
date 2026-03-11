---
name: speak-reference-architecture
description: |
  Implement Speak reference architecture with best-practice project layout for language learning apps.
  Use when designing new Speak integrations, reviewing project structure,
  or establishing architecture standards for language learning applications.
  Trigger with phrases like "speak architecture", "speak best practices",
  "speak project structure", "how to organize speak", "speak layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Speak Reference Architecture

## Overview
Production-ready architecture patterns for Speak language learning integrations.

## Prerequisites
- Understanding of layered architecture
- Speak SDK knowledge
- TypeScript project setup
- Testing framework configured

## Instructions
1. **Project Structure**
2. **Layer Architecture**
3. **Key Components**
4. **Data Flow Diagram**
5. **Configuration Management**
6. **Flagship Skills**

For full implementation details, load: `Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Structured project layout
- Client wrapper with caching
- Error boundary implemented
- Health checks configured
- Session management

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Circular dependencies | Wrong layering | Separate concerns by layer |
| Config not loading | Wrong paths | Verify config file locations |
| Type errors | Missing types | Add Speak types |
| Test isolation | Shared state | Use dependency injection |

## Examples
### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/speak/{handlers}
mkdir -p src/lessons src/speech src/progress
mkdir -p src/services/speak src/api/speak src/jobs/speak
mkdir -p tests/{unit,integration,fixtures}/speak
mkdir -p config docs/speak

touch src/speak/{client,config,types,errors}.ts
touch src/lessons/{session,conversation,pronunciation,vocabulary}.ts
touch src/speech/{recognizer,scorer,audio}.ts
```

## Resources
- [Speak SDK Documentation](https://developer.speak.com/sdk)
- [Speak Best Practices](https://developer.speak.com/docs/best-practices)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)