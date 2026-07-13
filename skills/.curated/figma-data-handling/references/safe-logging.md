# Step 5: Safe Logging

Deep-dive reference for the `figma-data-handling` skill — extracted from the 'Step 5: Safe Logging' step of the workflow.

```typescript
// Never log these fields from Figma responses
const REDACT_FIELDS = ['email', 'img_url', 'access_token', 'refresh_token'];

function safeFigmaLog(label: string, data: any) {
  const safe = JSON.parse(JSON.stringify(data));

  function redact(obj: any) {
    for (const key of Object.keys(obj)) {
      if (REDACT_FIELDS.includes(key)) {
        obj[key] = '[REDACTED]';
      } else if (typeof obj[key] === 'object' && obj[key] !== null) {
        redact(obj[key]);
      }
    }
  }

  redact(safe);
  console.log(`[figma] ${label}:`, JSON.stringify(safe));
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
