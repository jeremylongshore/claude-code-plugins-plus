---
name: abridge-reference-architecture
description: |
  Implement Abridge reference architecture for clinical AI integration.
  Use when designing a new Abridge deployment, reviewing project structure,
  or planning multi-site health system rollouts with EHR integration.
  Trigger: "abridge architecture", "abridge project structure",
  "abridge system design", "abridge multi-site".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, healthcare, ai, abridge, architecture]
compatible-with: claude-code
---

# Abridge Reference Architecture

## Overview

Reference architecture for Abridge clinical AI integration in a multi-site health system. Covers data flow, component design, EHR integration patterns, and HIPAA-compliant infrastructure.

## System Architecture

```
                    Health System Network
┌──────────────────────────────────────────────────────┐
│                                                       │
│  ┌─────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │ Provider │───▶│ Abridge App  │───▶│ Integration  │ │
│  │ Device   │    │ (Ambient AI) │    │ Service      │ │
│  │ (mobile/ │    │              │    │ (your code)  │ │
│  │ desktop) │    └──────┬───────┘    └──────┬───────┘ │
│  └─────────┘           │                    │         │
│                        │                    │         │
│              ┌─────────▼─────────┐          │         │
│              │ Abridge Cloud API │          │         │
│              │ (Partner API)     │          │         │
│              │ - Session mgmt    │          │         │
│              │ - Note generation │          │         │
│              │ - Patient summary │          │         │
│              └─────────┬─────────┘          │         │
│                        │                    │         │
│              ┌─────────▼─────────┐  ┌──────▼───────┐ │
│              │ Webhook Events    │  │ EHR System   │ │
│              │ - Note completed  │──│ (Epic/Athena)│ │
│              │ - Quality alerts  │  │ FHIR R4 API  │ │
│              └───────────────────┘  └──────────────┘ │
│                                                       │
└──────────────────────────────────────────────────────┘
```

## Project Structure

```
abridge-integration/
├── src/
│   ├── config/
│   │   ├── abridge.ts           # Abridge API configuration
│   │   ├── ehr.ts               # EHR/FHIR endpoint config
│   │   └── index.ts             # Environment-based config loader
│   ├── abridge/
│   │   ├── client.ts            # API client singleton
│   │   ├── errors.ts            # HIPAA-safe error handling
│   │   ├── retry.ts             # Retry with backoff
│   │   └── session-manager.ts   # Encounter session lifecycle
│   ├── ehr/
│   │   ├── fhir-client.ts       # FHIR R4 API wrapper
│   │   ├── epic-adapter.ts      # Epic-specific mappings
│   │   ├── athena-adapter.ts    # Athena-specific mappings
│   │   └── note-pusher.ts       # DocumentReference creation
│   ├── webhooks/
│   │   ├── handler.ts           # Express webhook endpoint
│   │   ├── signature.ts         # HMAC signature verification
│   │   ├── event-router.ts      # Event type → handler mapping
│   │   └── idempotency.ts       # Duplicate event prevention
│   ├── security/
│   │   ├── audit-logger.ts      # HIPAA audit trail
│   │   ├── phi-redactor.ts      # PHI detection and redaction
│   │   ├── rbac.ts              # Role-based access control
│   │   └── tls-config.ts        # TLS 1.3 enforcement
│   ├── monitoring/
│   │   ├── health.ts            # Health check endpoint
│   │   ├── metrics.ts           # Performance metrics collector
│   │   └── alerts.ts            # Quality and latency alerts
│   └── server.ts                # Express server entry point
├── tests/
│   ├── unit/                    # Unit tests (no API calls)
│   ├── integration/             # Sandbox API tests
│   └── fhir-validation/         # FHIR resource schema tests
├── fixtures/
│   └── transcripts/             # Synthetic encounter transcripts
├── scripts/
│   ├── deploy-cloud-run.sh      # GCP Cloud Run deployment
│   ├── readiness-check.ts       # Production readiness validation
│   └── diagnostic.sh            # Debug data collection
├── Dockerfile                   # HIPAA-compliant container
├── .env.example                 # Environment template (no secrets)
└── package.json
```

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Language | TypeScript | Type safety for healthcare data |
| EHR adapter | Strategy pattern | Swap EHR backends without changing core |
| Error handling | Custom error class | HIPAA-safe: never log PHI |
| Authentication | SMART on FHIR | Standard for healthcare OAuth |
| Deployment | Cloud Run | HIPAA BAA, auto-scaling, managed |
| Secrets | GCP Secret Manager | HIPAA-compliant, audited access |
| Monitoring | Custom health endpoint | Abridge + FHIR connectivity checks |

## Data Flow

```
1. Provider opens encounter on device
2. Abridge app captures ambient audio
3. Audio streams to Abridge Cloud via WebSocket
4. Real-time transcript fragments returned
5. Provider closes encounter
6. Abridge generates structured clinical note (10-30s)
7. Webhook fires: encounter.session.completed
8. Integration service fetches note via API
9. Note pushed to EHR via FHIR DocumentReference
10. Patient summary generated and pushed to portal
11. Provider reviews, edits, and signs note in EHR
12. Webhook fires: encounter.note.signed
```

## Multi-Site Deployment

```typescript
// src/config/multi-site.ts
interface SiteConfig {
  siteId: string;
  siteName: string;
  ehrType: 'epic' | 'athena' | 'cerner';
  fhirBaseUrl: string;
  abridgeOrgId: string;
  specialties: string[];
  providerCount: number;
  goLiveDate: Date;
}

const sites: SiteConfig[] = [
  {
    siteId: 'main-campus',
    siteName: 'Main Hospital',
    ehrType: 'epic',
    fhirBaseUrl: 'https://fhir.main-hospital.epic.com/interconnect-fhir-oauth',
    abridgeOrgId: 'org_main_campus',
    specialties: ['internal_medicine', 'cardiology', 'pulmonology'],
    providerCount: 200,
    goLiveDate: new Date('2026-06-01'),
  },
  {
    siteId: 'community-clinic',
    siteName: 'Community Clinic Network',
    ehrType: 'athena',
    fhirBaseUrl: 'https://api.athenahealth.com/fhir/r4',
    abridgeOrgId: 'org_community',
    specialties: ['family_medicine', 'pediatrics'],
    providerCount: 50,
    goLiveDate: new Date('2026-09-01'),
  },
];
```

## Output

- Complete project structure for Abridge integration
- EHR adapter pattern supporting Epic, Athena, and Cerner
- Multi-site deployment configuration
- End-to-end data flow documentation

## Resources

- [Abridge Platform](https://www.abridge.com/product)
- [Abridge Clinician App](https://www.abridge.com/platform/clinicians)
- [FHIR R4 Specification](https://hl7.org/fhir/R4/)
- [Epic FHIR APIs](https://fhir.epic.com/)
- [GCP Healthcare API](https://cloud.google.com/healthcare-api)

## Next Steps

Start implementation with `abridge-install-auth`, then follow the skill sequence through production deployment.
