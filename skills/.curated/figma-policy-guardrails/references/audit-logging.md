# Step 5: Audit Logging

Deep-dive reference for the `figma-policy-guardrails` skill — extracted from the 'Step 5: Audit Logging' step of the workflow.

```typescript
// Log all Figma API operations for compliance
interface FigmaAuditEntry {
  timestamp: string;
  action: string;
  endpoint: string;
  fileKey?: string;
  status: number;
  userId?: string;
}

function auditFigmaCall(entry: Omit<FigmaAuditEntry, 'timestamp'>) {
  const log: FigmaAuditEntry = {
    ...entry,
    timestamp: new Date().toISOString(),
  };

  // Structured log for aggregation
  console.log(JSON.stringify({ type: 'figma_audit', ...log }));
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
