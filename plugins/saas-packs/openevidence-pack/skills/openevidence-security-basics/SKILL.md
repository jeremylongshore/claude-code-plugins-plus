---
name: openevidence-security-basics
description: |
  Security Basics for OpenEvidence.
  Trigger: "openevidence security basics".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, openevidence, healthcare]
compatible-with: claude-code
---

# OpenEvidence Security Basics

## Overview
OpenEvidence provides AI-powered clinical evidence synthesis that processes protected health information (PHI), patient queries, and medical literature references. Integrations must comply with HIPAA requirements for PHI handling, audit logging, and access controls. A breach exposes patient health questions, clinical recommendations, and potentially identifiable medical conditions. Every API interaction must be treated as a HIPAA-regulated transaction.

## API Key Management
```typescript
function createOpenEvidenceClient(): { apiKey: string; baseUrl: string } {
  const apiKey = process.env.OPENEVIDENCE_API_KEY;
  if (!apiKey) {
    throw new Error("Missing OPENEVIDENCE_API_KEY — store in HIPAA-compliant secrets manager");
  }
  // PHI-adjacent access — enforce audit logging on every request
  console.log("OpenEvidence client initialized (key suffix:", apiKey.slice(-4), ")");
  return { apiKey, baseUrl: "https://api.openevidence.com/v1" };
}
```

## Webhook Signature Verification
```typescript
import crypto from "crypto";
import { Request, Response, NextFunction } from "express";

function verifyOpenEvidenceWebhook(req: Request, res: Response, next: NextFunction): void {
  const signature = req.headers["x-openevidence-signature"] as string;
  const secret = process.env.OPENEVIDENCE_WEBHOOK_SECRET!;
  const expected = crypto.createHmac("sha256", secret).update(req.body).digest("hex");
  if (!signature || !crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected))) {
    res.status(401).send("Invalid signature");
    return;
  }
  next();
}
```

## Input Validation
```typescript
import { z } from "zod";

const ClinicalQuerySchema = z.object({
  query_id: z.string().uuid(),
  clinical_question: z.string().min(10).max(2000),
  specialty: z.enum(["oncology", "cardiology", "neurology", "general", "pediatrics", "emergency"]).optional(),
  evidence_level: z.enum(["systematic_review", "rct", "cohort", "case_report", "expert_opinion"]).optional(),
  include_guidelines: z.boolean().default(true),
});

function validateClinicalQuery(data: unknown) {
  return ClinicalQuerySchema.parse(data);
}
```

## Data Protection
```typescript
const OPENEVIDENCE_PHI_FIELDS = ["patient_name", "date_of_birth", "mrn", "clinical_question", "diagnosis", "medication_list"];

function redactOpenEvidenceLog(record: Record<string, unknown>): Record<string, unknown> {
  const redacted = { ...record };
  for (const field of OPENEVIDENCE_PHI_FIELDS) {
    if (field in redacted) redacted[field] = "[REDACTED_PHI]";
  }
  return redacted;
}
```

## Security Checklist
- [ ] API keys stored in HIPAA-compliant secrets manager
- [ ] Separate keys per environment (dev/staging/prod)
- [ ] Key rotation scheduled quarterly
- [ ] HIPAA audit logging enabled on every API call
- [ ] PHI never logged in application logs (field-level redaction)
- [ ] BAA (Business Associate Agreement) on file with OpenEvidence
- [ ] Clinical query data encrypted at rest and in transit (TLS 1.2+)
- [ ] Access controls enforce minimum necessary PHI exposure

## Error Handling
| Vulnerability | Risk | Mitigation |
|---|---|---|
| Leaked API key | Unauthorized access to clinical evidence queries | HIPAA-compliant secrets manager + rotation |
| PHI in application logs | HIPAA violation and patient data exposure | Mandatory PHI field redaction |
| Missing BAA | Regulatory non-compliance penalty | BAA signed before integration goes live |
| Unencrypted clinical data | PHI breach during transit or storage | TLS 1.2+ in transit, AES-256 at rest |
| Missing audit trail | HIPAA audit failure | Immutable audit logs for all API interactions |

## Resources
- [OpenEvidence](https://www.openevidence.com)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)

## Next Steps
See `openevidence-prod-checklist`.
