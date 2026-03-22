---
name: abridge-core-workflow-a
description: |
  Implement Abridge ambient clinical documentation capture-to-note pipeline.
  Use when building the primary encounter workflow: audio capture, real-time
  transcription, AI note generation, and EHR note insertion.
  Trigger: "abridge clinical workflow", "abridge encounter pipeline",
  "ambient documentation workflow", "abridge note generation".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, healthcare, ai, abridge, clinical-documentation]
compatible-with: claude-code
---

# Abridge Core Workflow A — Encounter-to-Note Pipeline

## Overview

Primary money-path workflow for Abridge: capturing a clinical encounter via ambient listening, processing it through Abridge's generative AI, producing a structured clinical note, and pushing it into the EHR. This is the workflow that runs millions of times daily across health systems using Abridge.

## Prerequisites

- Completed `abridge-install-auth` setup
- EHR integration configured (Epic preferred)
- Audio capture infrastructure (microphone array or mobile device)
- HIPAA-compliant transport layer (TLS 1.3+)

## Instructions

### Step 1: Initialize Encounter Session

```typescript
// src/workflows/encounter-pipeline.ts
import axios, { AxiosInstance } from 'axios';

interface EncounterContext {
  patient_id: string;           // FHIR Patient resource ID
  encounter_id: string;         // FHIR Encounter resource ID
  provider_id: string;          // NPI or FHIR Practitioner ID
  specialty: string;            // e.g., 'internal_medicine', 'cardiology'
  encounter_type: 'outpatient' | 'inpatient' | 'emergency';
  department_id?: string;
  language: string;             // ISO 639-1 (Abridge supports 28+ languages)
}

interface SessionResponse {
  session_id: string;
  websocket_url: string;        // For real-time audio streaming
  status: 'initialized' | 'recording' | 'processing' | 'completed';
  created_at: string;
}

async function initializeEncounter(
  api: AxiosInstance,
  context: EncounterContext
): Promise<SessionResponse> {
  const { data } = await api.post('/encounters/sessions', {
    ...context,
    capture_mode: 'ambient',       // Background listening, no wake word
    note_template: 'soap',         // SOAP, H&P, progress note, etc.
    real_time_preview: true,       // Enable live note preview during encounter
    smart_phrases_enabled: true,   // Support Epic SmartPhrases in output
  });

  console.log(`Encounter session initialized: ${data.session_id}`);
  console.log(`WebSocket URL: ${data.websocket_url}`);
  return data;
}
```

### Step 2: Stream Audio via WebSocket

```typescript
// src/workflows/audio-stream.ts
import WebSocket from 'ws';

interface AudioStreamConfig {
  sampleRate: 16000;      // 16kHz required
  channels: 1;            // Mono
  encoding: 'pcm_s16le';  // 16-bit PCM little-endian
  chunkDurationMs: 100;   // Send 100ms chunks
}

interface TranscriptFragment {
  type: 'transcript_fragment';
  speaker: 'provider' | 'patient' | 'unknown';
  text: string;
  confidence: number;
  timestamp_ms: number;
  is_final: boolean;
}

interface NotePreview {
  type: 'note_preview';
  sections: Record<string, string>;
  last_updated: string;
}

function streamEncounterAudio(
  wsUrl: string,
  audioSource: NodeJS.ReadableStream
): Promise<void> {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(wsUrl, {
      headers: {
        'Authorization': `Bearer ${process.env.ABRIDGE_CLIENT_SECRET}`,
        'X-Org-Id': process.env.ABRIDGE_ORG_ID!,
      },
    });

    ws.on('open', () => {
      console.log('Audio stream connected');

      // Stream audio chunks
      audioSource.on('data', (chunk: Buffer) => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(chunk);
        }
      });

      audioSource.on('end', () => {
        ws.send(JSON.stringify({ type: 'end_of_stream' }));
      });
    });

    ws.on('message', (data: Buffer) => {
      const msg = JSON.parse(data.toString());

      if (msg.type === 'transcript_fragment') {
        const frag = msg as TranscriptFragment;
        if (frag.is_final) {
          console.log(`[${frag.speaker}]: ${frag.text}`);
        }
      }

      if (msg.type === 'note_preview') {
        const preview = msg as NotePreview;
        console.log('Live note preview updated:', Object.keys(preview.sections).join(', '));
      }
    });

    ws.on('close', () => resolve());
    ws.on('error', reject);
  });
}

export { streamEncounterAudio, AudioStreamConfig };
```

### Step 3: Generate and Retrieve Clinical Note

```typescript
// src/workflows/note-generation.ts
interface ClinicalNote {
  note_id: string;
  session_id: string;
  template: 'soap' | 'hp' | 'progress' | 'procedure';
  sections: {
    chief_complaint: string;
    history_present_illness: string;
    review_of_systems: string;
    physical_exam: string;
    assessment: string;
    plan: string;
    medications?: string;
    allergies?: string;
  };
  coding: {
    icd10: Array<{ code: string; description: string; confidence: number }>;
    cpt: Array<{ code: string; description: string; confidence: number }>;
    hcc: Array<{ code: string; raf_score: number }>;  // Risk adjustment
  };
  source_map: Array<{
    section: string;
    note_text: string;
    source_transcript: string;
    audio_start_ms: number;
    audio_end_ms: number;
  }>;
  quality_metrics: {
    confidence_score: number;
    completeness_score: number;
    coding_accuracy: number;
  };
}

async function generateAndRetrieveNote(
  api: AxiosInstance,
  sessionId: string
): Promise<ClinicalNote> {
  // Finalize session and trigger note generation
  await api.post(`/encounters/sessions/${sessionId}/finalize`);

  // Poll for completed note (typically 10-30 seconds)
  for (let i = 0; i < 60; i++) {
    const { data } = await api.get(`/encounters/sessions/${sessionId}/note`);
    if (data.status === 'completed') {
      return data.note;
    }
    await new Promise(r => setTimeout(r, 1000));
  }
  throw new Error(`Note generation timed out for session ${sessionId}`);
}
```

### Step 4: Push Note to EHR via FHIR

```typescript
// src/workflows/ehr-push.ts
import axios from 'axios';

interface FhirDocumentReference {
  resourceType: 'DocumentReference';
  status: 'current';
  type: { coding: Array<{ system: string; code: string; display: string }> };
  subject: { reference: string };
  context: { encounter: Array<{ reference: string }> };
  content: Array<{ attachment: { contentType: string; data: string } }>;
}

async function pushNoteToEpic(
  fhirBaseUrl: string,
  accessToken: string,
  note: { patient_id: string; encounter_id: string; content: string }
): Promise<string> {
  const docRef: FhirDocumentReference = {
    resourceType: 'DocumentReference',
    status: 'current',
    type: {
      coding: [{
        system: 'http://loinc.org',
        code: '11506-3',
        display: 'Progress note',
      }],
    },
    subject: { reference: `Patient/${note.patient_id}` },
    context: { encounter: [{ reference: `Encounter/${note.encounter_id}` }] },
    content: [{
      attachment: {
        contentType: 'text/plain',
        data: Buffer.from(note.content).toString('base64'),
      },
    }],
  };

  const response = await axios.post(
    `${fhirBaseUrl}/DocumentReference`,
    docRef,
    { headers: { Authorization: `Bearer ${accessToken}`, 'Content-Type': 'application/fhir+json' } }
  );

  console.log(`Note pushed to Epic: DocumentReference/${response.data.id}`);
  return response.data.id;
}
```

## Output

- Ambient encounter session with real-time transcription
- Structured SOAP note with ICD-10, CPT, and HCC codes
- Source-mapped citations linking AI output to conversation audio
- FHIR DocumentReference created in Epic EHR

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| WebSocket disconnect | Network instability | Implement reconnection with buffered audio |
| Empty transcript | Microphone not capturing | Verify audio input device and sample rate |
| Low confidence score | Background noise | Use directional mic or noise cancellation |
| FHIR push `422` | Invalid resource format | Validate FHIR R4 schema before POST |
| Note generation timeout | Complex multi-specialty encounter | Increase timeout; split into segments |

## Resources

- [Abridge Clinician Platform](https://www.abridge.com/platform/clinicians)
- [FHIR R4 DocumentReference](https://hl7.org/fhir/R4/documentreference.html)
- [Epic FHIR API](https://fhir.epic.com/)

## Next Steps

For patient-facing summaries and portal integration, see `abridge-core-workflow-b`.
