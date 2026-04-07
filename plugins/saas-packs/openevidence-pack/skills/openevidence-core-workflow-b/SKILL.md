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

# OpenEvidence — Evidence Review & Citations

## Overview

Search medical evidence, manage citations, and generate formatted evidence reports
through OpenEvidence. Use this workflow to find clinical studies for a specific
question, build citation collections for literature reviews, or produce structured
evidence summaries with graded recommendations. This is the secondary workflow —
for DeepConsult research synthesis, see `openevidence-core-workflow-a`.

## Instructions

### Step 1: Search the Evidence Database

```typescript
const results = await client.evidence.search({
  query: 'SGLT2 inhibitors cardiovascular outcomes type 2 diabetes',
  filters: {
    study_type: ['rct', 'meta_analysis', 'systematic_review'],
    year_range: { min: 2020, max: 2026 },
    evidence_level: ['1a', '1b', '2a'],
  },
  limit: 25,
  sort: 'relevance',
});
console.log(`Found ${results.total} studies`);
results.items.forEach(s =>
  console.log(`  [${s.evidence_level}] ${s.title} (${s.journal}, ${s.year}) — ${s.citations} citations`)
);
```

### Step 2: Build a Citation Collection

```typescript
const collection = await client.citations.create({
  name: 'SGLT2i CV Outcomes Review — April 2026',
  study_ids: results.items.slice(0, 15).map(s => s.id),
  tags: ['cardiology', 'diabetes', 'sglt2i'],
});
console.log(`Collection ${collection.id}: ${collection.study_count} studies`);
await client.citations.addByDoi(collection.id, { doi: '10.1056/NEJMoa2034577' });
```

### Step 3: Grade Evidence and Extract Key Findings

```typescript
const graded = await client.evidence.grade(collection.id, {
  framework: 'GRADE',  // GRADE | Oxford | USPSTF
  outcome: 'major_adverse_cardiovascular_events',
});
graded.findings.forEach(f =>
  console.log(`${f.outcome}: ${f.grade} (${f.certainty}) — ${f.summary}`)
);
console.log(`Overall recommendation: ${graded.recommendation}`);
```

### Step 4: Generate a Formatted Evidence Report

```typescript
const report = await client.reports.generate({
  collection_id: collection.id,
  format: 'structured',
  sections: ['clinical_question', 'search_strategy', 'evidence_table', 'grade_summary', 'references'],
  citation_style: 'AMA',
});
console.log(`Report generated: ${report.page_count} pages`);
console.log(`Download: ${report.download_url}`);
```

## HIPAA Notice

- HIPAA-compliant and SOC 2 Type II certified — never include patient identifiers
- Use de-identified clinical scenarios only; ensure BAA is in place before handling PHI

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Invalid API key or expired session | Regenerate key in OpenEvidence dashboard |
| `404 Study not found` | DOI not indexed or incorrect ID | Search by title or check DOI format |
| `422 Invalid filter` | Unsupported evidence_level or study_type | Use allowed values from `client.schema.filters()` |
| `429 Rate limited` | Exceeded 60 queries/minute | Add backoff; batch searches where possible |
| `503 Grading unavailable` | GRADE engine under maintenance | Retry after 5 minutes or use Oxford framework |

## Output

A successful workflow returns ranked evidence results with evidence levels, a curated
citation collection, GRADE assessments with certainty ratings, and a downloadable
structured report in AMA citation format.

## Resources

- [OpenEvidence Platform](https://www.openevidence.com)

## Next Steps

See `openevidence-sdk-patterns` for authentication and HIPAA-compliant configuration.
