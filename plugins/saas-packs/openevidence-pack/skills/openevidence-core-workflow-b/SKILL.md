---
name: openevidence-core-workflow-b
description: |
  Execute OpenEvidence DeepConsult workflow for comprehensive medical research.
  Use when implementing deep research synthesis, complex clinical questions,
  or when physicians need extensive literature review.
  Trigger with phrases like "openevidence deepconsult", "deep research",
  "comprehensive evidence", "literature synthesis".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# OpenEvidence Core Workflow B: DeepConsult Research

## Overview
Execute comprehensive medical evidence synthesis using OpenEvidence DeepConsult API. Build multi-source literature reviews, generate evidence summaries with confidence levels, and create structured clinical decision support outputs.

## Prerequisites
- OpenEvidence API key with DeepConsult access
- Understanding of medical evidence hierarchies
- Familiarity with clinical question formats (PICO)
- Output template for clinical summaries

## Instructions

### Step 1: Structure Clinical Questions (PICO Format)
```typescript
interface ClinicalQuestion {
  population: string;     // Patient population
  intervention: string;   // Treatment or exposure
  comparison?: string;    // Alternative treatment
  outcome: string;        // Desired outcome
  studyType?: string;     // RCT, meta-analysis, cohort
}

function formatPICOQuery(q: ClinicalQuestion): string {
  let query = `In ${q.population}, does ${q.intervention}`;
  if (q.comparison) query += ` compared to ${q.comparison}`;
  query += ` improve ${q.outcome}?`;
  return query;
}

// Example
const question: ClinicalQuestion = {
  population: 'adults with type 2 diabetes',
  intervention: 'GLP-1 receptor agonists',
  comparison: 'DPP-4 inhibitors',
  outcome: 'cardiovascular outcomes',
};
```

### Step 2: Execute DeepConsult Query
```typescript
const OPENEVIDENCE_API = 'https://api.openevidence.com/v1';

async function deepConsult(query: string, options?: {
  maxSources?: number;
  evidenceLevel?: 'all' | 'high-quality' | 'rct-only';
  recencyYears?: number;
}) {
  const response = await fetch(`${OPENEVIDENCE_API}/deepconsult`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${process.env.OPENEVIDENCE_API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query,
      max_sources: options?.maxSources || 20,
      evidence_filter: options?.evidenceLevel || 'all',
      recency_years: options?.recencyYears || 5,
    }),
  });

  if (!response.ok) throw new Error(`DeepConsult error: ${response.status}`);
  return response.json();
}
```

### Step 3: Process and Structure Evidence
```typescript
interface EvidenceSummary {
  question: string;
  conclusion: string;
  confidenceLevel: 'high' | 'moderate' | 'low' | 'very-low';
  keyFindings: string[];
  sources: Array<{
    title: string;
    authors: string;
    journal: string;
    year: number;
    evidenceType: string;
    url?: string;
  }>;
  limitations: string[];
}

function processDeepConsultResponse(response: any): EvidenceSummary {
  return {
    question: response.query,
    conclusion: response.synthesis?.conclusion || '',
    confidenceLevel: mapConfidence(response.synthesis?.confidence),
    keyFindings: response.synthesis?.key_findings || [],
    sources: (response.citations || []).map((c: any) => ({
      title: c.title,
      authors: c.authors?.join(', ') || 'Unknown',
      journal: c.journal || 'Unknown',
      year: c.year || 0,
      evidenceType: c.study_type || 'Unknown',
      url: c.doi ? `https://doi.org/${c.doi}` : undefined,
    })),
    limitations: response.synthesis?.limitations || [],
  };
}

function mapConfidence(score: number): EvidenceSummary['confidenceLevel'] {
  if (score >= 0.8) return 'high';
  if (score >= 0.6) return 'moderate';
  if (score >= 0.4) return 'low';
  return 'very-low';
}
```

### Step 4: Generate Clinical Summary Report
```typescript
function generateReport(summary: EvidenceSummary): string {
  const lines = [
    `# Evidence Summary`,
    ``,
    `**Question:** ${summary.question}`,
    ``,
    `## Conclusion (Confidence: ${summary.confidenceLevel})`,
    summary.conclusion,
    ``,
    `## Key Findings`,
    ...summary.keyFindings.map((f, i) => `${i + 1}. ${f}`),
    ``,
    `## Sources (${summary.sources.length})`,
    ...summary.sources.map(s =>
      `- ${s.authors} (${s.year}). *${s.title}*. ${s.journal}. [${s.evidenceType}]`
    ),
    ``,
    `## Limitations`,
    ...summary.limitations.map(l => `- ${l}`),
  ];

  return lines.join('\n');
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| No results returned | Query too narrow | Broaden population or outcome criteria |
| Low confidence score | Insufficient evidence | Expand recency window or evidence filter |
| API timeout | Complex multi-source query | Increase timeout, reduce maxSources |
| Missing citations | Paywalled sources | Use DOI links for source verification |

## Examples

### Quick Evidence Lookup
```typescript
const query = formatPICOQuery({
  population: 'elderly patients with atrial fibrillation',
  intervention: 'direct oral anticoagulants',
  comparison: 'warfarin',
  outcome: 'stroke prevention',
});

const result = await deepConsult(query, { evidenceLevel: 'high-quality' });
const summary = processDeepConsultResponse(result);
console.log(generateReport(summary));
```

## Resources
- [OpenEvidence API](https://docs.openevidence.com)
- [GRADE Evidence Framework](https://www.gradeworkinggroup.org/)
- [PICO Framework Guide](https://guides.lib.uw.edu/research/pico)
