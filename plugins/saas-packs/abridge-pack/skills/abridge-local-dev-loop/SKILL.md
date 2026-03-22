---
name: abridge-local-dev-loop
description: |
  Configure Abridge local development with FHIR server, synthetic data, and hot reload.
  Use when setting up a development environment for clinical AI integration,
  testing encounter workflows locally, or iterating on EHR integration code.
  Trigger: "abridge local dev", "abridge dev setup", "abridge test locally".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(docker:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, healthcare, ai, abridge, development]
compatible-with: claude-code
---

# Abridge Local Dev Loop

## Overview

Local development workflow for Abridge clinical AI integrations. Uses a local HAPI FHIR server for EHR simulation, synthetic patient data from Synthea, and Abridge sandbox APIs. Never use real PHI in development.

## Prerequisites

- Completed `abridge-install-auth` setup
- Docker installed (for local FHIR server)
- Node.js 18+ with TypeScript
- Abridge sandbox credentials

## Instructions

### Step 1: Start Local FHIR Server

```bash
# Run HAPI FHIR R4 server locally
docker run -d --name hapi-fhir \
  -p 8080:8080 \
  -e hapi.fhir.default_encoding=json \
  hapiproject/hapi:latest

# Verify
curl -s http://localhost:8080/fhir/metadata | jq '.fhirVersion'
# → "4.0.1"

# Seed synthetic patient
curl -X POST http://localhost:8080/fhir/Patient \
  -H "Content-Type: application/fhir+json" \
  -d '{"resourceType":"Patient","name":[{"given":["Jane"],"family":"Doe"}],"birthDate":"1985-03-15","gender":"female"}'
```

### Step 2: Create Dev Environment Configuration

```typescript
// src/config/dev.ts
interface DevConfig {
  abridge: { baseUrl: string; clientSecret: string; orgId: string };
  fhir: { baseUrl: string };
  fixtures: { transcriptsDir: string };
}

const devConfig: DevConfig = {
  abridge: {
    baseUrl: process.env.ABRIDGE_SANDBOX_URL || 'https://sandbox.api.abridge.com/v1',
    clientSecret: process.env.ABRIDGE_CLIENT_SECRET!,
    orgId: process.env.ABRIDGE_ORG_ID!,
  },
  fhir: { baseUrl: 'http://localhost:8080/fhir' },
  fixtures: { transcriptsDir: './fixtures/transcripts' },
};

export default devConfig;
```

### Step 3: Build Transcript Fixtures

```typescript
// fixtures/transcripts/index.ts
export const CARDIOLOGY_VISIT = {
  specialty: 'cardiology',
  segments: [
    { speaker: 'provider', text: 'I see you are here for a blood pressure follow-up.', timestamp_ms: 0 },
    { speaker: 'patient', text: 'Yes, I have been taking the lisinopril like you prescribed.', timestamp_ms: 3500 },
    { speaker: 'provider', text: 'Your BP today is 138 over 85. Better, but still elevated. Let us increase lisinopril from 10 to 20mg.', timestamp_ms: 7200 },
    { speaker: 'patient', text: 'Okay. Should I be worried?', timestamp_ms: 15000 },
    { speaker: 'provider', text: 'Not at all. Come back in four weeks.', timestamp_ms: 18000 },
  ],
};

export const DERMATOLOGY_VISIT = {
  specialty: 'dermatology',
  segments: [
    { speaker: 'provider', text: 'What brings you in today?', timestamp_ms: 0 },
    { speaker: 'patient', text: 'I have this mole on my back that has been changing color.', timestamp_ms: 2500 },
    { speaker: 'provider', text: 'How long has it been changing? Any itching or bleeding?', timestamp_ms: 5000 },
    { speaker: 'patient', text: 'About three months. It itches sometimes.', timestamp_ms: 8000 },
    { speaker: 'provider', text: 'The borders look irregular. I want to do a biopsy today.', timestamp_ms: 12000 },
  ],
};
```

### Step 4: Dev Test Runner with Watch Mode

```typescript
// src/dev/test-encounter.ts
import devConfig from '../config/dev';
import { CARDIOLOGY_VISIT } from '../../fixtures/transcripts';
import axios from 'axios';

async function runDevEncounter() {
  const api = axios.create({
    baseURL: devConfig.abridge.baseUrl,
    headers: {
      'Authorization': `Bearer ${devConfig.abridge.clientSecret}`,
      'X-Org-Id': devConfig.abridge.orgId,
    },
  });

  const { data: session } = await api.post('/encounters/sessions', {
    patient_id: 'demo-patient-001',
    provider_id: 'demo-provider-001',
    encounter_type: 'outpatient',
    specialty: CARDIOLOGY_VISIT.specialty,
    sandbox: true,
  });

  for (const seg of CARDIOLOGY_VISIT.segments) {
    await api.post(`/encounters/sessions/${session.session_id}/transcript`, seg);
  }

  await api.post(`/encounters/sessions/${session.session_id}/finalize`);

  // Poll for note
  for (let i = 0; i < 30; i++) {
    const { data } = await api.get(`/encounters/sessions/${session.session_id}/note`);
    if (data.status === 'completed') {
      console.log(JSON.stringify(data.note.sections, null, 2));
      // Push to local FHIR
      await axios.post(`${devConfig.fhir.baseUrl}/DocumentReference`, {
        resourceType: 'DocumentReference',
        status: 'current',
        content: [{ attachment: { contentType: 'text/plain', data: Buffer.from(JSON.stringify(data.note.sections)).toString('base64') } }],
      });
      console.log('Note pushed to local FHIR server');
      return;
    }
    await new Promise(r => setTimeout(r, 2000));
  }
}

runDevEncounter().catch(console.error);
```

### Step 5: Package Scripts

```json
{
  "scripts": {
    "dev:fhir": "docker start hapi-fhir 2>/dev/null || docker run -d --name hapi-fhir -p 8080:8080 hapiproject/hapi:latest",
    "dev:encounter": "tsx watch src/dev/test-encounter.ts",
    "dev:all": "npm run dev:fhir && npm run dev:encounter",
    "test:fixtures": "vitest run --grep 'fixture'"
  }
}
```

## Output

- Local HAPI FHIR R4 server on port 8080
- Synthetic patient data seeded
- Specialty-specific transcript fixtures
- Watch-mode dev loop with live note generation

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Docker port conflict | Port 8080 in use | `docker stop hapi-fhir && docker rm hapi-fhir` |
| Sandbox rate limit | Too many test sessions | Wait 60s between test runs |
| FHIR validation error | Malformed resource | Validate against FHIR R4 schema |

## Resources

- [HAPI FHIR Server](https://hapifhir.io/)
- [Synthea Patient Generator](https://synthetichealth.github.io/synthea/)

## Next Steps

For reusable SDK patterns, see `abridge-sdk-patterns`.
