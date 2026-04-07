---
name: openevidence-core-workflow-a
description: |
  Execute OpenEvidence primary workflow: Clinical Query & Decision Support.
  Trigger: "openevidence clinical query & decision support", "primary openevidence workflow".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, openevidence, healthcare]
compatible-with: claude-code
---

# OpenEvidence — Evidence Search & Retrieval

## Overview

Primary workflow for OpenEvidence clinical evidence integration. Covers the core use
case: searching clinical literature with evidence-level filters, retrieving structured
citations with journal and year metadata, checking drug interactions against patient
context, and looking up specialty guidelines from major bodies (ACC/AHA, ESC, NICE).
Responses include confidence scores and evidence grading to support clinical decision
making. All queries support specialty filtering to narrow results to relevant domains.

## Instructions

### Step 1: Search Clinical Evidence

```typescript
const result = await client.query({
  question: 'What is the recommended treatment for acute migraine in adults?',
  context: 'emergency_department',
  evidence_level: 'high',
  specialty: 'neurology',
  max_citations: 10,
});

console.log('Answer:', result.answer);
console.log(`Confidence: ${result.confidence} | Evidence grade: ${result.grade}`);
result.citations.forEach(c =>
  console.log(`  [${c.journal}] ${c.title} (${c.year}) — Level ${c.evidence_level}`)
);
```

### Step 2: Filter by Specialty and Date

```typescript
const recent = await client.search({
  keywords: 'GLP-1 receptor agonist cardiovascular outcomes',
  specialty: 'cardiology',
  year_min: 2024,
  evidence_level: 'meta-analysis',
  limit: 20,
});
console.log(`Found ${recent.total} results`);
recent.results.forEach(r => console.log(`  ${r.title} (${r.journal}, ${r.year})`));
```

### Step 3: Check Drug Interactions

```typescript
const interactions = await client.interactions.check({
  medications: ['metformin', 'lisinopril', 'atorvastatin'],
  patient_context: { age: 65, conditions: ['diabetes', 'hypertension'] },
});

interactions.forEach(i =>
  console.log(`${i.drug1} + ${i.drug2}: ${i.severity} — ${i.description}`)
);
if (interactions.some(i => i.severity === 'major')) {
  console.warn('WARNING: Major interaction detected — review before prescribing');
}
```

### Step 4: Guideline Lookup

```typescript
const guidelines = await client.guidelines.search({
  condition: 'hypertension',
  source: ['ACC/AHA', 'ESC', 'NICE'],
  year_min: 2023,
});
guidelines.forEach(g =>
  console.log(`${g.source}: ${g.title} (${g.year}) — ${g.recommendation_class}`)
);
```

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Invalid API key | Verify key in `Authorization: Bearer` header |
| `404 Not Found` | Unknown specialty code | Use standard specialty slugs from `/specialties` |
| `422 Validation` | Conflicting filter params | Remove mutually exclusive filters |
| `429 Rate Limited` | Exceeds 30 queries/min | Back off per `Retry-After` header |
| Empty citations array | Question too narrow | Broaden search terms or lower evidence level |

## Output

A successful run returns evidence-backed answers with citations, drug interaction
severity assessments, and guideline recommendations. Each response includes a
confidence score and evidence grade for clinical decision support.

## Resources

- [OpenEvidence Platform](https://www.openevidence.com)
- [OpenEvidence API Documentation](https://docs.openevidence.com)

## Next Steps

Continue with `openevidence-core-workflow-b` for patient case analysis and reporting.
