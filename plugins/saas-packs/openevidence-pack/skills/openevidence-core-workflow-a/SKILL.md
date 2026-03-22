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

# OpenEvidence — Clinical Query & Decision Support

## Overview
Primary workflow for OpenEvidence integration.

## Instructions

### Step 1: Clinical Query
```typescript
const result = await client.query({
  question: 'What is the recommended treatment for acute migraine in adults?',
  context: 'emergency_department',
  evidence_level: 'high',  // Filter by evidence quality
  max_citations: 10
});

console.log('Answer:', result.answer);
console.log('Confidence:', result.confidence);
result.citations.forEach(c =>
  console.log(`  [${c.journal}] ${c.title} (${c.year}) — ${c.evidence_level}`)
);
```

### Step 2: Drug Interaction Check
```typescript
const interactions = await client.interactions.check({
  medications: ['metformin', 'lisinopril', 'atorvastatin'],
  patient_context: { age: 65, conditions: ['diabetes', 'hypertension'] }
});

interactions.forEach(i =>
  console.log(`${i.drug1} + ${i.drug2}: ${i.severity} — ${i.description}`)
);
```

### Step 3: Guideline Lookup
```typescript
const guidelines = await client.guidelines.search({
  condition: 'hypertension',
  source: ['ACC/AHA', 'ESC'],
  year_min: 2023
});
guidelines.forEach(g =>
  console.log(`${g.source}: ${g.title} (${g.year})`)
);
```

## Resources
- [OpenEvidence Docs](https://www.openevidence.com)

## Next Steps
See `openevidence-core-workflow-b`.
