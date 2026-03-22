---
name: abridge-core-workflow-b
description: |
  Implement Abridge patient-facing documentation and after-visit summary generation.
  Use when building patient portal integration, generating plain-language summaries,
  multi-language translations, or after-visit instructions from clinical encounters.
  Trigger: "abridge patient summary", "after-visit summary", "patient portal abridge",
  "abridge patient-facing", "abridge multilingual".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, healthcare, ai, abridge, patient-engagement]
compatible-with: claude-code
---

# Abridge Core Workflow B — Patient-Facing Documentation

## Overview

Secondary workflow: generating plain-language patient summaries from the same clinical encounter captured in Workflow A. Abridge produces both clinician notes and patient-friendly after-visit summaries (AVS), supporting 28+ languages and multiple reading levels.

## Prerequisites

- Completed `abridge-core-workflow-a` (encounter-to-note pipeline)
- Patient portal integration configured (Epic MyChart, Athena Patient Portal)
- Understanding of health literacy requirements

## Instructions

### Step 1: Request Patient Summary from Completed Session

```typescript
// src/workflows/patient-summary.ts
import axios, { AxiosInstance } from 'axios';

interface PatientSummary {
  summary_id: string;
  session_id: string;
  language: string;                    // ISO 639-1 code
  reading_level: 'basic' | 'intermediate' | 'advanced';
  sections: {
    visit_reason: string;              // Plain-language chief complaint
    what_we_discussed: string;         // Key discussion points
    your_diagnosis: string;            // Explained at target reading level
    next_steps: string;                // Action items for patient
    medications: Array<{
      name: string;
      instructions: string;           // "Take 1 pill by mouth twice daily"
      warnings: string;
    }>;
    follow_up: {
      when: string;                    // "Come back in 2 weeks"
      why: string;                     // "To check if your cough improved"
      scheduling_instructions: string;
    };
    questions_to_ask: string[];        // AI-suggested questions for next visit
  };
  source_encounter: {
    date: string;
    provider_name: string;
    department: string;
  };
}

async function generatePatientSummary(
  api: AxiosInstance,
  sessionId: string,
  language: string = 'en',
  readingLevel: PatientSummary['reading_level'] = 'basic'
): Promise<PatientSummary> {
  const { data } = await api.post(`/encounters/sessions/${sessionId}/patient-summary`, {
    language,
    reading_level: readingLevel,
    include_medications: true,
    include_follow_up: true,
    include_suggested_questions: true,
  });

  return data;
}
```

### Step 2: Push to Patient Portal via FHIR

```typescript
// src/workflows/patient-portal-push.ts
interface FhirCommunication {
  resourceType: 'Communication';
  status: 'completed';
  category: Array<{ coding: Array<{ system: string; code: string }> }>;
  subject: { reference: string };
  encounter: { reference: string };
  payload: Array<{ contentString: string }>;
  sent: string;
}

async function pushToMyChart(
  fhirBaseUrl: string,
  accessToken: string,
  summary: {
    patient_id: string;
    encounter_id: string;
    content: string;
    language: string;
  }
): Promise<string> {
  const communication: FhirCommunication = {
    resourceType: 'Communication',
    status: 'completed',
    category: [{
      coding: [{
        system: 'http://terminology.hl7.org/CodeSystem/communication-category',
        code: 'notification',
      }],
    }],
    subject: { reference: `Patient/${summary.patient_id}` },
    encounter: { reference: `Encounter/${summary.encounter_id}` },
    payload: [{ contentString: summary.content }],
    sent: new Date().toISOString(),
  };

  const response = await axios.post(
    `${fhirBaseUrl}/Communication`,
    communication,
    { headers: { Authorization: `Bearer ${accessToken}` } }
  );

  return response.data.id;
}
```

### Step 3: Multi-Language Translation

```typescript
// src/workflows/translation.ts
// Abridge supports 28+ languages natively — no external translation service needed

const SUPPORTED_LANGUAGES = [
  'en', 'es', 'zh', 'ar', 'vi', 'ko', 'tl', 'ru', 'fr', 'pt',
  'hi', 'de', 'ja', 'it', 'pl', 'ur', 'fa', 'bn', 'pa', 'gu',
  'ha', 'yo', 'am', 'so', 'sw', 'ne', 'my', 'th',
] as const;

async function generateMultiLanguageSummaries(
  api: AxiosInstance,
  sessionId: string,
  languages: string[]
): Promise<Map<string, PatientSummary>> {
  const summaries = new Map<string, PatientSummary>();

  // Generate summaries in parallel for requested languages
  const results = await Promise.allSettled(
    languages.map(lang =>
      generatePatientSummary(api, sessionId, lang, 'basic')
    )
  );

  results.forEach((result, index) => {
    if (result.status === 'fulfilled') {
      summaries.set(languages[index], result.value);
    } else {
      console.error(`Translation failed for ${languages[index]}:`, result.reason);
    }
  });

  return summaries;
}
```

### Step 4: Format After-Visit Summary (AVS)

```typescript
// src/workflows/avs-formatter.ts
function formatAfterVisitSummary(summary: PatientSummary): string {
  const lines: string[] = [
    `AFTER-VISIT SUMMARY`,
    `Date: ${summary.source_encounter.date}`,
    `Provider: ${summary.source_encounter.provider_name}`,
    `Department: ${summary.source_encounter.department}`,
    '',
    `WHY YOU CAME IN`,
    summary.sections.visit_reason,
    '',
    `WHAT WE DISCUSSED`,
    summary.sections.what_we_discussed,
    '',
    `YOUR DIAGNOSIS`,
    summary.sections.your_diagnosis,
    '',
    `WHAT TO DO NEXT`,
    summary.sections.next_steps,
  ];

  if (summary.sections.medications.length > 0) {
    lines.push('', 'YOUR MEDICATIONS');
    for (const med of summary.sections.medications) {
      lines.push(`  ${med.name}: ${med.instructions}`);
      if (med.warnings) lines.push(`    Important: ${med.warnings}`);
    }
  }

  lines.push(
    '',
    'FOLLOW-UP',
    `When: ${summary.sections.follow_up.when}`,
    `Why: ${summary.sections.follow_up.why}`,
    summary.sections.follow_up.scheduling_instructions,
  );

  return lines.join('\n');
}
```

## Output

- Patient-friendly after-visit summary at target reading level
- Multi-language translations (28+ languages supported)
- FHIR Communication resource pushed to patient portal
- Formatted AVS document with medications, follow-up, and next steps

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Unsupported language | Language not in Abridge's 28+ set | Check `SUPPORTED_LANGUAGES` list |
| Summary too vague | Encounter transcript was short | Ensure encounter has enough clinical detail |
| MyChart push `403` | Patient portal not linked | Verify patient has active MyChart account |
| Missing medications | Provider didn't discuss meds | Medications only included if mentioned in encounter |

## Resources

- [Abridge Platform](https://www.abridge.com/product)
- [FHIR R4 Communication Resource](https://hl7.org/fhir/R4/communication.html)
- [Health Literacy Guidelines (CDC)](https://www.cdc.gov/healthliteracy/)
- [Epic MyChart Integration](https://mychart.epic.com/)

## Next Steps

For common integration errors, see `abridge-common-errors`.
