---
name: speak-security-basics
description: |
  Security best practices for Speak API keys, audio data privacy, student data protection, and COPPA/FERPA compliance.
  Use when implementing security basics features,
  or troubleshooting Speak language learning integration issues.
  Trigger with phrases like "speak security basics", "speak security basics".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, speak, api]

---
# Speak Security Basics

## Overview
Security best practices for Speak API keys, audio data privacy, student data protection, and COPPA/FERPA compliance.

## Prerequisites
- Completed `speak-install-auth` setup
- Valid API credentials configured
- ffmpeg installed for audio processing

## Instructions

### API Key Security
```bash
# Never commit API keys
echo '.env' >> .gitignore
echo '.env.local' >> .gitignore

# Use secrets manager in production
export SPEAK_API_KEY="$(aws secretsmanager get-secret-value --secret-id speak/api-key --query SecretString --output text)"
```

### Audio Data Privacy
```typescript
// Speak processes audio on their servers — do NOT store student audio locally
// unless required by your application
class PrivacyAwareClient {
  async assessAndClean(audioPath: string, targetText: string, language: string) {
    try {
      const result = await this.client.assessPronunciation({
        audioPath, targetText, language,
      });
      return result;
    } finally {
      // Delete local audio file after assessment
      fs.unlinkSync(audioPath);
    }
  }
}
```

### Student Data Protection
- Never log student audio recordings
- Redact student names from API logs
- Store assessment scores, not raw audio
- Implement data retention policies (delete after N days)
- COPPA compliance for students under 13: parental consent required
- FERPA compliance for educational institutions: student data agreements

### Security Checklist
- [ ] API keys in secrets manager, not code
- [ ] Audio files deleted after processing
- [ ] Student PII not logged
- [ ] HTTPS enforced for all API calls
- [ ] Rate limiting prevents abuse
- [ ] Access logs maintained for audit

## Output
- Basics implementation complete
- Speak API integration verified
- Production-ready patterns applied

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Invalid API key | Verify SPEAK_API_KEY environment variable |
| 429 Rate Limited | Too many requests | Wait Retry-After seconds, use backoff |
| Audio format error | Wrong codec/sample rate | Convert to WAV 16kHz mono with ffmpeg |
| Session expired | Timeout after 30 min | Start a new conversation session |

## Resources
- [Speak Website](https://speak.com)
- [OpenAI Realtime API](https://platform.openai.com/docs/guides/realtime)
- [Speak GPT-4 Blog](https://speak.com/blog/speak-gpt-4)

## Next Steps
See `speak-prod-checklist` for production readiness.

## Examples

**Basic**: Apply security basics with default configuration for a standard Speak integration.

**Advanced**: Customize for production with error recovery, monitoring, and team-specific requirements.
