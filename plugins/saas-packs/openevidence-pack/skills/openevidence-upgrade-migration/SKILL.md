---
name: openevidence-upgrade-migration
description: |
  Upgrade Migration for OpenEvidence.
  Trigger: "openevidence upgrade migration".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, openevidence, healthcare]
compatible-with: claude-code
---

# OpenEvidence Upgrade & Migration

## Overview

OpenEvidence is a clinical AI platform that provides evidence-based medical answers and clinical decision support. The API exposes endpoints for clinical queries, evidence retrieval, and citation management. Tracking API changes is critical because OpenEvidence evolves its evidence grading schema, citation format, and clinical query response structure — and breaking changes in a healthcare context can surface outdated medical evidence, alter confidence scores, or remove critical safety disclaimers that downstream clinical applications depend on.

## Version Detection

```typescript
const OPENEVIDENCE_BASE = "https://api.openevidence.com/v1";

async function detectOpenEvidenceVersion(apiKey: string): Promise<void> {
  const res = await fetch(`${OPENEVIDENCE_BASE}/status`, {
    headers: { Authorization: `Bearer ${apiKey}`, "Content-Type": "application/json" },
  });
  const version = res.headers.get("x-openevidence-api-version") ?? "v1";
  console.log(`OpenEvidence API version: ${version}`);

  // Test clinical query response schema
  const queryRes = await fetch(`${OPENEVIDENCE_BASE}/query`, {
    method: "POST",
    headers: { Authorization: `Bearer ${apiKey}`, "Content-Type": "application/json" },
    body: JSON.stringify({ question: "What is the recommended treatment for hypertension?", max_citations: 1 }),
  });
  const data = await queryRes.json();
  const hasStructuredCitations = data.citations?.[0]?.evidence_grade !== undefined;
  console.log(`Structured citations: ${hasStructuredCitations}`);
  const hasDisclaimers = data.disclaimers !== undefined;
  console.log(`Disclaimers field present: ${hasDisclaimers}`);
}
```

## Migration Checklist

- [ ] Review OpenEvidence release notes for API schema changes
- [ ] Verify clinical query response structure (answer, citations, confidence)
- [ ] Check evidence grading scale — letter grades vs. numeric scores may change
- [ ] Validate citation format (PMID references, DOI links, journal metadata)
- [ ] Test disclaimer and safety warning fields in query responses
- [ ] Update clinical specialty filters if taxonomy was expanded
- [ ] Check rate limits for clinical query endpoints (may differ by plan tier)
- [ ] Verify streaming response format if using real-time query mode
- [ ] Update evidence date range filters if temporal query syntax changed
- [ ] Run clinical validation suite against known question-answer pairs

## Schema Migration

```typescript
// OpenEvidence query response: flat answer → structured evidence with grading
interface OldQueryResponse {
  answer: string;
  citations: Array<{ title: string; url: string; source: string }>;
  confidence: number;
}

interface NewQueryResponse {
  answer: { text: string; sections: Array<{ heading: string; content: string }> };
  citations: Array<{
    title: string;
    url: string;
    source: string;
    pmid?: string;
    doi?: string;
    evidence_grade: "A" | "B" | "C" | "D" | "expert_opinion";
    publication_year: number;
  }>;
  confidence: { score: number; level: "high" | "moderate" | "low"; basis: string };
  disclaimers: string[];
  query_metadata: { specialty: string; guidelines_version: string };
}

function migrateQueryResponse(old: OldQueryResponse): NewQueryResponse {
  return {
    answer: { text: old.answer, sections: [{ heading: "Summary", content: old.answer }] },
    citations: old.citations.map((c) => ({
      ...c,
      evidence_grade: "C" as const,
      publication_year: 0,
    })),
    confidence: { score: old.confidence, level: old.confidence > 0.7 ? "high" : "moderate", basis: "legacy" },
    disclaimers: ["This information is for educational purposes. Consult a healthcare provider."],
    query_metadata: { specialty: "general", guidelines_version: "unknown" },
  };
}
```

## Rollback Strategy

```typescript
class OpenEvidenceClient {
  private apiVersion: "v1" | "v2";

  constructor(private apiKey: string, version: "v1" | "v2" = "v2") {
    this.apiVersion = version;
  }

  async query(question: string, options?: { specialty?: string }): Promise<any> {
    try {
      const res = await fetch(`https://api.openevidence.com/${this.apiVersion}/query`, {
        method: "POST",
        headers: { Authorization: `Bearer ${this.apiKey}`, "Content-Type": "application/json" },
        body: JSON.stringify({ question, ...options }),
      });
      if (!res.ok) throw new Error(`OpenEvidence ${res.status}`);
      return await res.json();
    } catch (err) {
      if (this.apiVersion === "v2") {
        console.warn("Falling back to OpenEvidence API v1");
        this.apiVersion = "v1";
        return this.query(question, options);
      }
      throw err;
    }
  }
}
```

## Error Handling

| Migration Issue | Symptom | Fix |
|----------------|---------|-----|
| Evidence grade scale changed | Grade returns `"level-1"` instead of `"A"` | Map new grade scale to internal representation using lookup table |
| Citation format restructured | Missing `pmid` field, now nested under `identifiers.pmid` | Update citation parser for new nested identifier structure |
| Disclaimer field required | Integration missing safety warnings in user-facing output | Always render `disclaimers[]` array from query response |
| Specialty taxonomy expanded | `400` with `unknown specialty` on filtered queries | Fetch current specialties from `/specialties` endpoint |
| Streaming format changed | SSE parser breaks on new event structure | Update event stream parser for new `data:` payload format |

## Resources

- [OpenEvidence](https://www.openevidence.com)
- [OpenEvidence API Documentation](https://docs.openevidence.com)

## Next Steps

For CI pipeline integration, see `openevidence-ci-integration`.
