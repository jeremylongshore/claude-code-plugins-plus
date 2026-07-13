# Step 4: Write to Target (Variables API)

Deep-dive reference for the `figma-migration-deep-dive` skill — extracted from the 'Step 4: Write to Target (Variables API)' step of the workflow.

```typescript
// Enterprise only: create variables in the target file
async function migrateToVariables(
  targetFileKey: string,
  tokens: MigrationToken[]
) {
  const colorTokens = tokens.filter(t => t.category === 'color');

  // Create variable collection and variables
  const payload = {
    variableCollections: [{
      action: 'CREATE' as const,
      id: 'temp_collection_1',
      name: 'Migrated Colors',
    }],
    variables: colorTokens.map((token, i) => ({
      action: 'CREATE' as const,
      id: `temp_var_${i}`,
      name: token.name.replace(/\//g, '/'), // preserve Figma group paths
      variableCollectionId: 'temp_collection_1',
      resolvedType: 'COLOR' as const,
      codeSyntax: { WEB: `--${token.name.toLowerCase().replace(/[\s/]+/g, '-')}` },
    })),
    variableModeValues: colorTokens.map((token, i) => ({
      variableId: `temp_var_${i}`,
      modeId: '', // Will use default mode
      value: {
        r: token.value.r / 255,
        g: token.value.g / 255,
        b: token.value.b / 255,
        a: token.value.a,
      },
    })),
  };

  const res = await fetch(
    `https://api.figma.com/v1/files/${targetFileKey}/variables`,
    {
      method: 'POST',
      headers: {
        'X-Figma-Token': PAT,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    }
  );

  if (!res.ok) throw new Error(`Variable creation failed: ${res.status} ${await res.text()}`);
  return res.json();
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
