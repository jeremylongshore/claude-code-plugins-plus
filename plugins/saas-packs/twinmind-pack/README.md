# TwinMind Skill Pack

> Claude Code skill pack for TwinMind AI meeting assistant integration (24 skills)

## Installation

```bash
/plugin install twinmind-pack@claude-code-plugins-plus
```

## About TwinMind

[TwinMind](https://twinmind.com) is an AI-powered "second brain" that captures and organizes your spoken knowledge. Built by ex-Google X scientists at ThirdEar AI Inc., TwinMind transcribes meetings, generates summaries, extracts action items, and builds a searchable memory vault of everything you've discussed. Raised $5.7M (seed round, Sept 2025).

**Key facts:**
- **Ear-3 speech model**: 5.26% Word Error Rate, 3.8% speaker diarization error, 140+ languages
- **Privacy-first**: On-device audio processing, no recordings stored, local transcripts with optional encrypted cloud backup
- **Multi-model AI**: Auto-routes to GPT-4, Claude, or Gemini based on task (summaries, quick answers, memory search)
- **Platforms**: Chrome extension, iOS, Android with two-way sync
- **Pricing**: Free (unlimited transcription) / Pro $10/mo / Enterprise (custom, on-premise)

## Skills Included

### Standard Skills (S01-S12)
| Skill | Description |
|-------|-------------|
| `twinmind-install-auth` | Install Chrome extension, mobile app, calendar integration |
| `twinmind-hello-world` | First meeting transcription with AI summary and action items |
| `twinmind-local-dev-loop` | Development workflow with TwinMind API integration |
| `twinmind-sdk-patterns` | Transcription patterns, memory vault queries, AI routing |
| `twinmind-core-workflow-a` | Meeting transcription and summary workflow |
| `twinmind-core-workflow-b` | Action item extraction and follow-up automation |
| `twinmind-common-errors` | Diagnose microphone, transcription, and sync errors |
| `twinmind-debug-bundle` | Audio diagnostics, API health, extension state |
| `twinmind-rate-limits` | API limits, context token management, model routing |
| `twinmind-security-basics` | On-device processing, encrypted backups, permissions |
| `twinmind-prod-checklist` | Production deployment and integration checklist |
| `twinmind-upgrade-migration` | Plan tier upgrades and feature migrations |

### Pro Skills (P13-P18)
| Skill | Description |
|-------|-------------|
| `twinmind-ci-integration` | CI pipeline for meeting workflow automation |
| `twinmind-deploy-integration` | Production deployment with API access |
| `twinmind-webhooks-events` | Meeting events, transcription completion, calendar sync |
| `twinmind-performance-tuning` | Ear-3 configuration, audio quality, caching |
| `twinmind-cost-tuning` | Tier selection, usage monitoring, cost optimization |
| `twinmind-reference-architecture` | Meeting AI pipeline architecture |

### Flagship Skills (F19-F24)
| Skill | Description |
|-------|-------------|
| `twinmind-multi-env-setup` | Dev/staging/prod environment configuration |
| `twinmind-observability` | Transcription quality, coverage, and vault health |
| `twinmind-incident-runbook` | Transcription failures, sync issues, recovery |
| `twinmind-data-handling` | GDPR compliance, data export, retention policies |
| `twinmind-enterprise-rbac` | On-premise, SSO, custom models, team sharing |
| `twinmind-migration-deep-dive` | Migrate from Otter.ai, Fireflies, Grain |

## Quick Start

1. Install Chrome extension from [Chrome Web Store](https://chromewebstore.google.com/detail/twinmind/agpbjhhcmoanaljagpoheldgjhclepdj)
2. Sign in with Google or email
3. Join a Google Meet, Zoom, or Teams call in your browser
4. Click TwinMind icon and "Start Transcribing"
5. After the meeting: review transcript, AI summary, and action items

## Ear-3 Speech Model

| Metric | Value | Industry Comparison |
|--------|-------|-------------------|
| Word Error Rate | 5.26% | Best in class |
| Speaker Diarization | 3.8% DER | Best in class |
| Languages | 140+ | Broadest coverage |
| Cost | $0.23/hour | Competitive |
| Latency | Real-time | On-device processing |

## Resources

- [TwinMind Website](https://twinmind.com)
- [Chrome Extension Tutorial](https://twinmind.com/ce-tutorial)
- [Ear-3 Model Announcement](https://www.marktechpost.com/2025/09/11/twinmind-introduces-ear-3-model/)
- [iOS App](https://apps.apple.com/us/app/twinmind-ai-notes-memory/id6504585781)
- [Android App](https://play.google.com/store/apps/details?id=ai.twinmind.android)

## License

MIT
