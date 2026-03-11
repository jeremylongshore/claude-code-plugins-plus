---
name: speak-security-basics
description: |
  Apply Speak security best practices for secrets, user data, and audio handling.
  Use when securing API keys, implementing user privacy controls,
  or auditing Speak security configuration.
  Trigger with phrases like "speak security", "speak secrets",
  "secure speak", "speak API key security", "speak privacy".
allowed-tools: Read, Write, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Speak Security Basics

## Overview
Security best practices for Speak API keys, user data, and audio content in language learning applications.

## Prerequisites
- Speak SDK installed
- Understanding of environment variables
- Access to Speak dashboard
- Knowledge of audio privacy concerns

## Instructions
1. **Security Checklist**

For full implementation details, load: `Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Secure API key storage
- Environment-specific access controls
- Audio privacy protection
- Webhook security enabled
- User data protection compliance

## Error Handling
| Security Issue | Detection | Mitigation |
|----------------|-----------|------------|
| Exposed API key | Git scanning, audit logs | Rotate immediately |
| Excessive scopes | Audit logs review | Reduce permissions |
| Missing rotation | Key age check | Schedule rotation |
| Audio leak | Access logs | Encrypt and restrict |
| Missing consent | Compliance audit | Update consent flow |

## Examples
### Service Account Pattern
```typescript
const clients = {
  lessons: new SpeakClient({
    apiKey: process.env.SPEAK_LESSON_KEY,
    appId: process.env.SPEAK_APP_ID,
  }),
  speech: new SpeakClient({
    apiKey: process.env.SPEAK_SPEECH_KEY,
    appId: process.env.SPEAK_APP_ID,
  }),
};
```

## Resources
- [Speak Security Guide](https://developer.speak.com/docs/security)
- [Speak API Scopes](https://developer.speak.com/docs/scopes)
- [Audio Privacy Best Practices](https://developer.speak.com/docs/audio-privacy)
- [GDPR Compliance](https://gdpr.eu/developers/)

## Next Steps
For production deployment, see `speak-prod-checklist`.
