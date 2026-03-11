---
name: openevidence-hello-world
description: |
  Create a minimal working OpenEvidence clinical query example.
  Use when starting a new OpenEvidence integration, testing your setup,
  or learning basic clinical query patterns.
  Trigger with phrases like "openevidence hello world", "openevidence example",
  "openevidence quick start", "first clinical query".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# OpenEvidence Hello World

## Overview
Minimal working example demonstrating core OpenEvidence clinical query functionality.

## Prerequisites
- Completed `openevidence-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
```typescript
// src/openevidence-demo.ts
import { OpenEvidenceClient } from '@openevidence/sdk';

const client = new OpenEvidenceClient({
  apiKey: process.env.OPENEVIDENCE_API_KEY,
  orgId: process.env.OPENEVIDENCE_ORG_ID,
});
```

### Step 2: Make Your First Clinical Query
```typescript
async function firstClinicalQuery() {
  // Simple clinical question
  const response = await client.query({
    question: "What are the first-line treatments for type 2 diabetes in adults?",
    context: {
      specialty: "internal-medicine",
      urgency: "routine",
    },
  });

  console.log('Answer:', response.answer);
  console.log('Sources:', response.citations.map(c => c.source));
  console.log('Confidence:', response.confidence);
}

firstClinicalQuery().catch(console.error);
```

### Step 3: Run the Example
```bash
# With TypeScript
npx ts-node src/openevidence-demo.ts

# With Node.js (after compilation)
node dist/openevidence-demo.js
```

## Output
- Working code file with OpenEvidence client initialization
- Successful API response with evidence-based answer
- Console output showing:
```
Answer: First-line treatment for type 2 diabetes in adults typically includes...
Sources: ["NEJM 2024", "ADA Standards of Care 2025", "JAMA Internal Medicine"]  # 2024: 2025 year
Confidence: 0.95
```

## Response Structure
```typescript
interface ClinicalQueryResponse {
  answer: string;              // Evidence-based clinical answer
  citations: Citation[];       // Peer-reviewed sources
  confidence: number;          // 0-1 confidence score
  lastUpdated: string;         // When evidence was last reviewed
  disclaimer: string;          // Clinical use disclaimer
  deepConsultAvailable: boolean; // Whether DeepConsult can provide more detail
}

interface Citation {
  source: string;              // Journal/guideline name
  title: string;               // Article title
  authors: string[];           // Author list
  year: number;                // Publication year
  doi?: string;                // DOI if available
  url?: string;                // Link to source
}
```

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Import Error | SDK not installed | Verify with `npm list @openevidence/sdk` |
| Auth Error | Invalid credentials | Check environment variables are set |
| Timeout | Complex query or network issues | Increase timeout or retry |
| Rate Limit | Too many requests | Wait and retry with exponential backoff |
| Invalid Query | Question not clinical | Ensure query is medically relevant |

## Examples

### TypeScript Example with Error Handling
```typescript
import { OpenEvidenceClient, OpenEvidenceError } from '@openevidence/sdk';

const client = new OpenEvidenceClient({
  apiKey: process.env.OPENEVIDENCE_API_KEY,
  orgId: process.env.OPENEVIDENCE_ORG_ID,
});

async function queryClinicalEvidence(question: string) {
  try {
    const response = await client.query({
      question,
      context: {
        specialty: "family-medicine",
        urgency: "routine",
      },
      options: {
        maxCitations: 5,
        includeGuidelines: true,
      },
    });

    return {
      answer: response.answer,
      sources: response.citations,
      confidence: response.confidence,
    };
  } catch (error) {
    if (error instanceof OpenEvidenceError) {
      console.error(`OpenEvidence Error [${error.code}]:`, error.message);
    }
    throw error;
  }
}

// Example usage
queryClinicalEvidence(
  "What is the recommended antibiotic for community-acquired pneumonia?"
).then(result => {
  console.log('Clinical Answer:', result.answer);
  console.log('Evidence Sources:', result.sources.length);
});
```

### Python Example
```python
from openevidence import OpenEvidenceClient, OpenEvidenceError

client = OpenEvidenceClient()

def query_clinical_evidence(question: str) -> dict:
    try:
        response = client.query(
            question=question,
            context={
                "specialty": "emergency-medicine",
                "urgency": "urgent"
            }
        )

        return {
            "answer": response.answer,
            "sources": [c.source for c in response.citations],
            "confidence": response.confidence
        }
    except OpenEvidenceError as e:
        print(f"Error [{e.code}]: {e.message}")
        raise

# Example usage
result = query_clinical_evidence(
    "What are the contraindications for tPA in acute ischemic stroke?"
)
print(f"Answer: {result['answer']}")
```

## Resources
- [OpenEvidence](https://www.openevidence.com/)
- [OpenEvidence API Terms](https://www.openevidence.com/policies/api)

## Next Steps
Proceed to `openevidence-local-dev-loop` for development workflow setup.