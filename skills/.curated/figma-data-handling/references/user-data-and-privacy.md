# Step 3: User Data and Privacy

Deep-dive reference for the `figma-data-handling` skill — extracted from the 'Step 3: User Data and Privacy' step of the workflow.

```typescript
// GET /v1/me -- returns authenticated user
interface FigmaUser {
  id: string;
  handle: string;
  img_url: string;
  email: string;   // PII -- handle carefully
}

// Redact PII before logging or storing
function redactFigmaUser(user: FigmaUser): Omit<FigmaUser, 'email'> & { email: string } {
  return {
    ...user,
    email: '[REDACTED]',
    img_url: '[REDACTED]',
  };
}

// Data classification for Figma responses
interface DataClassification {
  field: string;
  sensitivity: 'public' | 'internal' | 'pii';
  handling: string;
}

const figmaDataClassification: DataClassification[] = [
  { field: 'user.email', sensitivity: 'pii', handling: 'Encrypt at rest, redact in logs' },
  { field: 'user.handle', sensitivity: 'internal', handling: 'Do not expose to unauthorized users' },
  { field: 'user.img_url', sensitivity: 'pii', handling: 'Do not cache without consent' },
  { field: 'file.name', sensitivity: 'internal', handling: 'Standard handling' },
  { field: 'comment.message', sensitivity: 'internal', handling: 'May contain PII -- scan before storing' },
  { field: 'PAT token', sensitivity: 'pii', handling: 'Never log, never store in code' },
];
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
