# Speak Skill Pack

> Claude Code skill pack for Speak AI language learning platform integration (24 skills)

## Installation

```bash
/plugin install speak-pack@claude-code-plugins-plus
```

## About Speak

[Speak](https://speak.com) is an AI-powered language learning platform that gets users speaking from day one. Built on OpenAI's GPT-4o and Realtime API, Speak provides real-time pronunciation feedback, adaptive AI tutoring, and conversation practice without a live tutor. Backed by OpenAI Startup Fund, Founders Fund, and Y Combinator. Valued at $1B+ (Series C, 2024).

**Key facts:**
- 14+ supported languages (Korean, Spanish, Japanese, French, German, and more)
- GPT-4o for conversation generation and personalized feedback
- OpenAI Whisper + proprietary models for speech recognition
- Realtime API for sub-second response times in live roleplays
- Proficiency graph system tracks learner knowledge state

## Skills Included

### Standard Skills (S01-S12)
| Skill | Description |
|-------|-------------|
| `speak-install-auth` | Install SDK, configure API keys, set up speech pipeline |
| `speak-hello-world` | First AI tutoring session with pronunciation scoring |
| `speak-local-dev-loop` | Mock tutors, audio fixtures, debug mode |
| `speak-sdk-patterns` | Session manager, audio preprocessor, retry, progress tracker |
| `speak-core-workflow-a` | AI conversation practice with adaptive feedback |
| `speak-core-workflow-b` | Pronunciation drills with phoneme-level analysis |
| `speak-common-errors` | Error codes, diagnostic commands, recovery patterns |
| `speak-debug-bundle` | Auth check, audio validator, network diagnostics |
| `speak-rate-limits` | Throttled client, batch queue, tier limits |
| `speak-security-basics` | API key security, audio privacy, COPPA/FERPA |
| `speak-prod-checklist` | Audio pipeline, monitoring, compliance checklist |
| `speak-upgrade-migration` | SDK upgrades, API version migration |

### Pro Skills (P13-P18)
| Skill | Description |
|-------|-------------|
| `speak-ci-integration` | GitHub Actions with mocked API tests |
| `speak-deploy-integration` | Deploy to Vercel, Cloud Run, containers |
| `speak-webhooks-events` | Lesson completion and progress events |
| `speak-performance-tuning` | Audio preprocessing, caching, connection pooling |
| `speak-cost-tuning` | Usage monitoring, tier optimization |
| `speak-reference-architecture` | Client, API gateway, assessment engine, progress store |

### Flagship Skills (F19-F24)
| Skill | Description |
|-------|-------------|
| `speak-multi-env-setup` | Dev/staging/prod with separate keys and mock modes |
| `speak-observability` | API health, assessment latency, score distributions |
| `speak-incident-runbook` | Outage triage, offline fallback, recovery |
| `speak-data-handling` | Audio privacy, GDPR/COPPA compliance |
| `speak-enterprise-rbac` | SSO, teacher/student roles, class management |
| `speak-migration-deep-dive` | Platform migration, progress import |

## Quick Start

```typescript
import { SpeakClient } from '@speak/language-sdk';

const client = new SpeakClient({
  apiKey: process.env.SPEAK_API_KEY!,
  appId: process.env.SPEAK_APP_ID!,
  language: 'es',
});

// Start conversation practice
const session = await client.startConversation({
  scenario: 'ordering-food',
  language: 'es',
  level: 'intermediate',
});
console.log('Tutor:', session.firstPrompt.text);

// Assess pronunciation
const result = await client.assessPronunciation({
  audioPath: './recording.wav',
  targetText: 'Hola, como estas?',
  language: 'es',
  detailLevel: 'phoneme',
});
console.log(`Score: ${result.score}/100`);
```

## Resources

- [Speak Website](https://speak.com)
- [Speak GPT-4 Blog](https://speak.com/blog/speak-gpt-4)
- [OpenAI Realtime API](https://platform.openai.com/docs/guides/realtime)
- [Live Roleplays Feature](https://speak.com/blog/live-roleplays)

## License

MIT
