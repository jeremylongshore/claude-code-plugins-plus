# Abridge Skill Pack

> Claude Code skills for Abridge clinical AI integration — ambient documentation, EHR integration, HIPAA-compliant workflows (18 skills)

Abridge is the leading ambient AI platform for clinical documentation, used by major health systems (Northwell, WVU Medicine, Emory, UI Health). Named Best in KLAS for Ambient AI (2025, 2026). These skills cover the full integration lifecycle: EHR connectivity (Epic, Athena, Cerner), FHIR R4 note push, patient-facing summaries, and HIPAA-compliant deployment.

## Installation

```bash
/plugin install abridge-pack@claude-code-plugins-plus
```

## Skills Included

### Standard Skills (S01-S12)

| Skill | What It Does |
|-------|-------------|
| `abridge-install-auth` | Configure partner API credentials and SMART on FHIR OAuth |
| `abridge-hello-world` | Create encounter session, submit transcript, receive clinical note |
| `abridge-local-dev-loop` | Local HAPI FHIR server + synthetic data + watch mode dev loop |
| `abridge-sdk-patterns` | Type-safe API client, HIPAA-safe error handling, retry logic |
| `abridge-core-workflow-a` | Full encounter pipeline: audio capture → transcription → SOAP note → EHR push |
| `abridge-core-workflow-b` | Patient-facing after-visit summaries, multi-language (28+ languages) |
| `abridge-common-errors` | Diagnose auth, session, audio, note generation, and FHIR errors |
| `abridge-debug-bundle` | Collect PHI-redacted diagnostic data for support tickets |
| `abridge-rate-limits` | Concurrent session management, 429 retry, usage monitoring |
| `abridge-security-basics` | TLS 1.3 enforcement, HIPAA audit logging, RBAC, secrets management |
| `abridge-prod-checklist` | Go-live readiness validation, rollback procedures, monitoring thresholds |
| `abridge-upgrade-migration` | API version upgrades, EHR migrations, note template migration |

### Pro Skills (P13-P18)

| Skill | What It Does |
|-------|-------------|
| `abridge-ci-integration` | GitHub Actions with PHI leak scanning, FHIR validation, sandbox tests |
| `abridge-deploy-integration` | HIPAA-compliant Cloud Run deployment with Secret Manager |
| `abridge-webhooks-events` | Handle note completion, quality alerts, provider enrollment events |
| `abridge-performance-tuning` | Audio streaming optimization, adaptive polling, FHIR batch push |
| `abridge-cost-tuning` | Provider utilization tracking, session waste detection, ROI calculator |
| `abridge-reference-architecture` | Multi-site health system architecture with EHR adapter pattern |

## Key Concepts

- **No public SDK** — Abridge integrates via partner REST APIs and EHR-embedded workflows
- **Epic Pal** — Abridge is Epic's first Pal partner; deepest EHR integration is with Epic
- **HIPAA mandatory** — All skills enforce PHI-safe logging, TLS 1.3, and audit trails
- **FHIR R4** — Notes pushed to EHR as DocumentReference; summaries as Communication resources
- **28+ languages** — Patient summaries support multilingual generation natively

## License

MIT
