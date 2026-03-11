---
name: openevidence-core-workflow-a
description: |
  Execute OpenEvidence clinical query workflow for point-of-care decisions.
  Use when implementing real-time clinical decision support,
  building EHR-integrated evidence lookups, or point-of-care queries.
  Trigger with phrases like "openevidence clinical query", "point of care",
  "quick clinical lookup", "evidence search".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# OpenEvidence Core Workflow A: Clinical Query

## Overview
Primary workflow for real-time clinical queries at the point of care. Returns evidence-based answers in 5-10 seconds with peer-reviewed citations.

## Prerequisites
- Completed `openevidence-install-auth` setup
- Understanding of clinical decision support patterns
- Valid API credentials configured

## Use Cases
- Drug interaction checks during prescribing
- Treatment protocol lookups
- Differential diagnosis support
- Dosing verification
- Clinical guideline queries

## Instructions

### Step 1: Structure the Clinical Query
```typescript
// src/workflows/clinical-query.ts
import { OpenEvidenceClient } from '@openevidence/sdk';

interface ClinicalQueryRequest {
  question: string;
  specialty: string;
  urgency: 'stat' | 'urgent' | 'routine';
  patientContext?: {
    age?: number;
    sex?: 'male' | 'female';
    conditions?: string[];
    medications?: string[];
  };
}

interface ClinicalQueryResponse {
  answer: string;
  citations: Citation[];
  confidence: number;
  responseTimeMs: number;
  queryId: string;
}

interface Citation {
  source: string;
  title: string;
  year: number;
  doi?: string;
  guideline?: boolean;
}
```

### Step 2: Implement Query Service
```typescript
// src/services/point-of-care-query.ts
import { OpenEvidenceClient } from '@openevidence/sdk';

const client = new OpenEvidenceClient({
  apiKey: process.env.OPENEVIDENCE_API_KEY,
  orgId: process.env.OPENEVIDENCE_ORG_ID,
  timeout: 15000, // 15 second timeout for point-of-care  # 15000 = configured value
});

export async function queryAtPointOfCare(
  request: ClinicalQueryRequest
): Promise<ClinicalQueryResponse> {
  const startTime = Date.now();

  const response = await client.query({
    question: request.question,
    context: {
      specialty: request.specialty,
      urgency: request.urgency,
      ...(request.patientContext && {
        patientAge: request.patientContext.age,
        patientSex: request.patientContext.sex,
        relevantConditions: request.patientContext.conditions,
        currentMedications: request.patientContext.medications,
      }),
    },
    options: {
      maxCitations: 5,
      includeGuidelines: true,
      prioritizeRecent: true, // Prefer evidence from last 3 years
    },
  });

  return {
    answer: response.answer,
    citations: response.citations.map(c => ({
      source: c.source,
      title: c.title,
      year: c.year,
      doi: c.doi,
      guideline: c.type === 'guideline',
    })),
    confidence: response.confidence,
    responseTimeMs: Date.now() - startTime,
    queryId: response.id,
  };
}
```

### Step 3: Drug Interaction Check Example
```typescript
// src/workflows/drug-interaction.ts
export async function checkDrugInteraction(
  drug1: string,
  drug2: string,
  patientContext?: { age?: number; conditions?: string[] }
): Promise<{
  hasInteraction: boolean;
  severity: 'major' | 'moderate' | 'minor' | 'none';
  details: string;
  citations: Citation[];
}> {
  const response = await queryAtPointOfCare({
    question: `What are the drug interactions between ${drug1} and ${drug2}?`,
    specialty: 'pharmacology',
    urgency: 'urgent',
    patientContext,
  });

  // Parse severity from response
  const severity = determineSeverity(response.answer);

  return {
    hasInteraction: severity !== 'none',
    severity,
    details: response.answer,
    citations: response.citations,
  };
}

function determineSeverity(answer: string): 'major' | 'moderate' | 'minor' | 'none' {
  const lower = answer.toLowerCase();
  if (lower.includes('contraindicated') || lower.includes('major interaction')) return 'major';
  if (lower.includes('moderate interaction') || lower.includes('caution')) return 'moderate';
  if (lower.includes('minor interaction')) return 'minor';
  if (lower.includes('no significant interaction') || lower.includes('no known interaction')) return 'none';
  return 'moderate'; // Default to moderate if unclear
}
```

### Step 4: EHR Integration Pattern
```typescript
// src/integrations/ehr-hook.ts
import { queryAtPointOfCare } from '../services/point-of-care-query';

// HL7 FHIR CDS Hooks integration
interface CDSRequest {
  hook: string;
  hookInstance: string;
  context: {
    patientId: string;
    encounterId?: string;
    medications?: any[];
  };
}

interface CDSResponse {
  cards: CDSCard[];
}

interface CDSCard {
  summary: string;
  detail: string;
  indicator: 'info' | 'warning' | 'critical';
  source: { label: string; url?: string };
  suggestions?: any[];
}

export async function handleCDSHook(request: CDSRequest): Promise<CDSResponse> {
  // Extract clinical context from FHIR resources
  const medications = request.context.medications?.map(m => m.medicationCodeableConcept?.text) || [];

  // Query OpenEvidence for relevant clinical information
  const evidence = await queryAtPointOfCare({
    question: buildClinicalQuestion(request.hook, medications),
    specialty: 'family-medicine',
    urgency: 'routine',
    patientContext: {
      medications,
    },
  });

  return {
    cards: [{
      summary: 'Clinical Evidence Available',
      detail: evidence.answer,
      indicator: evidence.confidence > 0.9 ? 'info' : 'warning',
      source: {
        label: 'OpenEvidence',
        url: 'https://openevidence.com',
      },
    }],
  };
}

function buildClinicalQuestion(hook: string, medications: string[]): string {
  switch (hook) {
    case 'medication-prescribe':
      return `Are there any drug interactions or contraindications for ${medications.join(', ')}?`;
    case 'order-sign':
      return `What are the clinical considerations for prescribing ${medications.join(', ')}?`;
    default:
      return `Provide clinical guidance for patient on ${medications.join(', ')}`;
  }
}
```

## Output
- Real-time clinical query response (5-10 seconds)
- Evidence-based answer with peer-reviewed citations
- Confidence score for clinical decision support
- Query audit trail for compliance

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Timeout | Complex query or network | Increase timeout, simplify question |
| Low confidence | Ambiguous query | Rephrase with more specific context |
| No citations | Rare condition | Consider DeepConsult for deeper research |
| Rate limit | Too many queries | Implement request queuing |

## Performance Considerations
- Target response time: < 10 seconds for point-of-care
- Cache frequent queries (drug info, guidelines)
- Pre-warm connections during low-traffic periods
- Use streaming responses for faster perceived performance

## Examples

### Complete Point-of-Care Integration
```typescript
// Example: Emergency department workflow
async function edClinicalSupport(chiefComplaint: string, vitals: any) {
  const queries = await Promise.all([
    queryAtPointOfCare({
      question: `What is the differential diagnosis for ${chiefComplaint}?`,
      specialty: 'emergency-medicine',
      urgency: 'stat',
    }),
    queryAtPointOfCare({
      question: `What workup is recommended for ${chiefComplaint}?`,
      specialty: 'emergency-medicine',
      urgency: 'stat',
    }),
  ]);

  return {
    differential: queries[0],
    workup: queries[1],
  };
}
```

## Resources
- [OpenEvidence](https://www.openevidence.com/)
- [HL7 CDS Hooks](https://cds-hooks.hl7.org/)
- [SMART on FHIR](https://smarthealthit.org/)

## Next Steps
For comprehensive research queries, see `openevidence-core-workflow-b` (DeepConsult).