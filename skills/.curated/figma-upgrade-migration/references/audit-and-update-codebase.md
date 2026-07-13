# Step 4: Audit and Update Codebase

Deep-dive reference for the `figma-upgrade-migration` skill — extracted from the 'Step 4: Audit and Update Codebase' step of the workflow.

```typescript
// Create a migration checker
function auditFigmaIntegration(codebasePaths: string[]) {
  const issues: string[] = [];

  // Check for deprecated scope usage
  // Check for V1 webhook endpoints
  // Check for old token format
  const patterns = [
    { pattern: 'files:read', message: 'Deprecated scope: use file_content:read' },
    { pattern: '/v1/webhooks', message: 'V1 webhooks: migrate to /v2/webhooks' },
    { pattern: 'X-FIGMA-TOKEN', message: 'Header is case-sensitive: use X-Figma-Token' },
  ];

  return { issues, patterns };
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
