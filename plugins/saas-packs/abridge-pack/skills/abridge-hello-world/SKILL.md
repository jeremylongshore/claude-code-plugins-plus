---
name: abridge-hello-world
description: |
  Create a minimal Abridge ambient AI clinical documentation example.
  Use when testing Abridge integration, verifying EHR connectivity,
  or learning how Abridge captures and structures clinical conversations.
  Trigger: "abridge hello world", "abridge example", "abridge quick start", "test abridge".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, healthcare, ai, abridge, clinical-documentation]
compatible-with: claude-code
---

# Abridge Hello World

## Overview

Minimal working example demonstrating Abridge's ambient clinical documentation. This creates a simulated encounter session, sends audio/transcript data, and receives a structured clinical note.

## Prerequisites

- Completed `abridge-install-auth` setup
- Abridge sandbox credentials configured
- Node.js 18+ with TypeScript

## Instructions

### Step 1: Create Project Structure

```bash
mkdir abridge-hello-world && cd abridge-hello-world
npm init -y
npm install axios dotenv typescript @types/node
npx tsc --init --target ES2022 --module NodeNext --moduleResolution NodeNext
```

### Step 2: Build the Encounter Session Client

```typescript
// src/encounter-session.ts
import axios, { AxiosInstance } from 'axios';

interface EncounterSession {
  session_id: string;
  patient_id: string;
  provider_id: string;
  encounter_type: 'outpatient' | 'inpatient' | 'emergency';
  status: 'active' | 'processing' | 'completed';
  created_at: string;
}

interface ClinicalNote {
  note_id: string;
  session_id: string;
  sections: {
    chief_complaint: string;
    history_present_illness: string;
    review_of_systems: string;
    physical_exam: string;
    assessment: string;
    plan: string;
  };
  icd10_codes: Array<{ code: string; description: string }>;
  cpt_codes: Array<{ code: string; description: string }>;
  confidence_score: number;
  source_citations: Array<{
    section: string;
    text: string;
    audio_timestamp_start: number;
    audio_timestamp_end: number;
  }>;
}

class AbridgeClient {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: process.env.ABRIDGE_SANDBOX_URL || 'https://sandbox.api.abridge.com/v1',
      headers: {
        'Authorization': `Bearer ${process.env.ABRIDGE_CLIENT_SECRET}`,
        'X-Org-Id': process.env.ABRIDGE_ORG_ID!,
        'Content-Type': 'application/json',
      },
      timeout: 30000,
    });
  }

  async createSession(
    patientId: string,
    providerId: string,
    encounterType: EncounterSession['encounter_type'] = 'outpatient'
  ): Promise<EncounterSession> {
    const { data } = await this.api.post('/sessions', {
      patient_id: patientId,
      provider_id: providerId,
      encounter_type: encounterType,
      specialty: 'internal_medicine',
      language: 'en',
    });
    return data;
  }

  async submitTranscript(sessionId: string, transcript: string): Promise<void> {
    await this.api.post(`/sessions/${sessionId}/transcript`, {
      text: transcript,
      format: 'plain_text',
    });
  }

  async generateNote(sessionId: string): Promise<ClinicalNote> {
    // Trigger note generation
    await this.api.post(`/sessions/${sessionId}/generate`);

    // Poll for completion (Abridge processes asynchronously)
    let attempts = 0;
    while (attempts < 30) {
      const { data: session } = await this.api.get(`/sessions/${sessionId}`);
      if (session.status === 'completed') {
        const { data: note } = await this.api.get(`/sessions/${sessionId}/note`);
        return note;
      }
      await new Promise(r => setTimeout(r, 2000));
      attempts++;
    }
    throw new Error('Note generation timed out after 60s');
  }
}

export { AbridgeClient, EncounterSession, ClinicalNote };
```

### Step 3: Run the Hello World Example

```typescript
// src/main.ts
import 'dotenv/config';
import { AbridgeClient } from './encounter-session';

// Sample clinical conversation transcript (de-identified)
const SAMPLE_TRANSCRIPT = `
Doctor: Good morning, what brings you in today?
Patient: I've been having this persistent cough for about two weeks now.
Doctor: Is it a dry cough or are you producing any sputum?
Patient: It's mostly dry, but sometimes I cough up a little clear mucus.
Doctor: Any fever, chills, or shortness of breath?
Patient: No fever, but I do feel a little short of breath when I climb stairs.
Doctor: Are you a smoker?
Patient: No, I quit about five years ago. I smoked for about ten years before that.
Doctor: Let me listen to your lungs. Take a deep breath... Okay, I hear some mild
  wheezing in both lung fields. Your oxygen saturation is 97%.
Doctor: I think this is likely a post-viral cough, possibly with some mild reactive
  airway disease given your smoking history. I'd like to start you on an inhaler
  and have you come back in two weeks. If the cough persists, we'll get a chest X-ray.
Patient: Sounds good, thank you.
`;

async function main() {
  const client = new AbridgeClient();

  // 1. Create encounter session
  console.log('Creating encounter session...');
  const session = await client.createSession('patient_demo_001', 'provider_demo_001');
  console.log(`Session created: ${session.session_id}`);

  // 2. Submit transcript
  console.log('Submitting transcript...');
  await client.submitTranscript(session.session_id, SAMPLE_TRANSCRIPT);
  console.log('Transcript submitted');

  // 3. Generate clinical note
  console.log('Generating clinical note (this may take 10-30 seconds)...');
  const note = await client.generateNote(session.session_id);

  console.log('\n=== Generated Clinical Note ===');
  console.log(`Chief Complaint: ${note.sections.chief_complaint}`);
  console.log(`Assessment: ${note.sections.assessment}`);
  console.log(`Plan: ${note.sections.plan}`);
  console.log(`\nICD-10 Codes: ${note.icd10_codes.map(c => c.code).join(', ')}`);
  console.log(`Confidence: ${(note.confidence_score * 100).toFixed(1)}%`);
  console.log(`Source Citations: ${note.source_citations.length} segments linked`);
}

main().catch(console.error);
```

## Output

- Encounter session created in Abridge sandbox
- Transcript processed through Abridge's ambient AI engine
- Structured SOAP note with ICD-10/CPT codes
- Source citations mapping AI output to conversation segments

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid sandbox credentials | Re-check `.env.local` credentials |
| `422 Invalid specialty` | Unsupported specialty code | Use supported values from API docs |
| Note generation timeout | Large/complex transcript | Increase polling timeout beyond 60s |
| Empty note sections | Transcript too short | Provide at least 30 seconds of conversation |
| Missing ICD codes | Ambiguous clinical content | Ensure transcript includes clear diagnoses |

## Resources

- [Abridge Product Overview](https://www.abridge.com/product)
- [Abridge AI Technology](https://www.abridge.com/ai)
- [HL7 FHIR Clinical Notes](https://hl7.org/fhir/clinicalnotes.html)

## Next Steps

Proceed to `abridge-local-dev-loop` for development workflow with live audio capture.
