---
name: speak-local-dev-loop
description: |
  Configure Speak local development with hot reload, testing, and mock tutors.
  Use when setting up a development environment, configuring test workflows,
  or establishing a fast iteration cycle with Speak language learning.
  Trigger with phrases like "speak dev setup", "speak local development",
  "speak dev environment", "develop with speak".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pnpm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Speak Local Dev Loop

## Overview
Set up a fast, reproducible local development workflow for Speak language learning integrations.

## Prerequisites
- Completed `speak-install-auth` setup
- Node.js 18+ with npm/pnpm
- Code editor with TypeScript support
- Git for version control
- Audio testing tools (optional)

## Instructions

1. For full implementation details, load: `Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Working development environment with hot reload
- Configured test suite with mocking
- Environment variable management
- Fast iteration cycle for Speak development
- Mock tutor for offline development

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Module not found | Missing dependency | Run `npm install` |
| Port in use | Another process | Kill process or change port |
| Env not loaded | Missing .env.local | Copy from .env.example |
| Test timeout | Slow network | Use mocks or increase timeout |
| Audio not playing | Browser security | Use HTTPS in dev |

## Examples
### Debug Mode with Verbose Logging
```bash
set -euo pipefail
# Enable verbose logging for Speak operations
DEBUG=speak:* npm run dev

# Log only speech recognition
DEBUG=speak:speech npm run dev

# Log tutor interactions
DEBUG=speak:tutor npm run dev
```

### Development Scripts
```json
{
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "dev:mock": "SPEAK_MOCK_MODE=true tsx watch src/index.ts",
    "test:unit": "vitest run tests/unit",
    "test:integration": "vitest run tests/integration",
    "lesson:spanish": "tsx src/lessons/spanish-basics.ts",
    "lesson:korean": "SPEAK_TARGET_LANGUAGE=ko tsx src/lessons/korean-basics.ts"
  }
}
```

## Resources
- [Speak SDK Reference](https://developer.speak.com/sdk)
- [Vitest Documentation](https://vitest.dev/)
- [tsx Documentation](https://github.com/esbuild-kit/tsx)
- [Web Speech API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API)

## Next Steps
See `speak-sdk-patterns` for production-ready code patterns.