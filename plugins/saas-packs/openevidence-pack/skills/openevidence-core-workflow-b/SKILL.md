---
name: openevidence-core-workflow-b
description: |
  Execute OpenEvidence secondary workflow: DeepConsult Research Synthesis.
  Trigger: "openevidence deepconsult research synthesis", "secondary openevidence workflow".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, openevidence, healthcare]
compatible-with: claude-code
---

# OpenEvidence — DeepConsult Research Synthesis

## Overview
Secondary workflow complementing the primary workflow.

## Instructions

### Step 1: Submit DeepConsult
```typescript
// DeepConsult: comprehensive research synthesis (async, takes minutes)
const consult = await client.deepConsult.create({
  question: 'What is the current evidence for GLP-1 agonists in heart failure with preserved ejection fraction?',
  depth: 'comprehensive',  // brief | standard | comprehensive
  include_meta_analyses: true,
  year_range: { min: 2020 }
});
console.log(`Consult ID: ${consult.id} | Status: ${consult.status}`);
```

### Step 2: Poll for Completion
```typescript
let result;
while (true) {
  result = await client.deepConsult.get(consult.id);
  if (result.status === 'completed') break;
  console.log(`Status: ${result.status} (${result.progress}%)`);
  await new Promise(r => setTimeout(r, 10_000));
}
```

### Step 3: Review Results
```typescript
console.log('Summary:', result.summary);
console.log('Key Findings:', result.key_findings.length);
result.key_findings.forEach(f =>
  console.log(`  - ${f.finding} [${f.evidence_level}] (${f.citations.length} refs)`)
);
console.log('Total references:', result.references.length);
```

### HIPAA Notice
- OpenEvidence is HIPAA-compliant and SOC 2 Type II certified
- Never include patient identifiers in API queries
- Use de-identified clinical scenarios only
- Ensure BAA is in place before handling PHI

## Resources
- [OpenEvidence Docs](https://www.openevidence.com)

## Next Steps
See `openevidence-common-errors`.
