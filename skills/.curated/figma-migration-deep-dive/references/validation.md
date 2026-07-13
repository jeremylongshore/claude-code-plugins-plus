# Step 5: Validation

Deep-dive reference for the `figma-migration-deep-dive` skill — extracted from the 'Step 5: Validation' step of the workflow.

```typescript
async function validateMigration(
  sourceFileKey: string,
  targetFileKey: string
): Promise<{ passed: boolean; issues: string[] }> {
  const sourceStyles = await extractAllStyles(sourceFileKey);
  const targetVars = await fetch(
    `https://api.figma.com/v1/files/${targetFileKey}/variables/local`,
    { headers: { 'X-Figma-Token': PAT } }
  ).then(r => r.json());

  const issues: string[] = [];
  const targetNames = new Set(
    Object.values(targetVars.meta.variables).map((v: any) => v.name)
  );

  for (const style of sourceStyles) {
    if (style.type === 'FILL' && !targetNames.has(style.name)) {
      issues.push(`Missing in target: ${style.name}`);
    }
  }

  return { passed: issues.length === 0, issues };
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
