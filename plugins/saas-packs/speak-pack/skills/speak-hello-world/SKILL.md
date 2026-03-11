---
name: speak-hello-world
description: |
  Create a minimal working Speak language learning example.
  Use when starting a new Speak integration, testing your setup,
  or learning basic Speak API patterns for language tutoring.
  Trigger with phrases like "speak hello world", "speak example",
  "speak quick start", "simple speak lesson".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Speak Hello World

## Overview
Minimal working example demonstrating core Speak functionality for AI-powered language learning.

## Prerequisites
- Completed `speak-install-auth` setup
- Valid API credentials configured
- Development environment ready
- Microphone access for speech input (optional for testing)

## Instructions

1. For full implementation details, load: `Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Working code file with Speak client initialization
- Successful lesson session creation
- AI tutor prompt and feedback displayed
- Console output showing:
```
AI Tutor says: Hola! Welcome to your Spanish lesson. Let's practice greetings. Can you say "Hello, my name is..." in Spanish?
Audio URL: https://speak.com/audio/abc123.mp3
Feedback: Great job! Your pronunciation was clear.
Pronunciation: 85
Grammar: [No corrections needed]
```

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Import Error | SDK not installed | Verify with `npm list @speak/language-sdk` |
| Auth Error | Invalid credentials | Check environment variables are set |
| Session Timeout | Exceeded lesson duration | Extend session or start new one |
| Rate Limit | Too many requests | Wait and retry with exponential backoff |
| Language Not Supported | Invalid language code | Use supported language codes |

## Examples
See `references/implementation-guide.md` for detailed examples.

## Resources
- [Speak Getting Started](https://developer.speak.com/docs/getting-started)
- [Speak API Reference](https://developer.speak.com/api)
- [Speak Lesson Types](https://developer.speak.com/docs/lesson-types)
- [Speech Recognition Guide](https://developer.speak.com/docs/speech-recognition)

## Next Steps
Proceed to `speak-local-dev-loop` for development workflow setup.