# Step 5: Use Variables API (Enterprise)

Deep-dive reference for the `figma-core-workflow-a` skill — extracted from the 'Step 5: Use Variables API (Enterprise)' step of the workflow.

```typescript
// GET /v1/files/:key/variables/local (Tier 2, requires file_variables:read)
const vars = await client.getLocalVariables(fileKey);

// vars.meta.variables: Record<variableId, Variable>
// vars.meta.variableCollections: Record<collectionId, Collection>
for (const [id, variable] of Object.entries(vars.meta.variables)) {
  const collection = vars.meta.variableCollections[variable.variableCollectionId];
  console.log(`${collection.name}/${variable.name}: ${variable.resolvedType}`);
  // resolvedType: "COLOR" | "FLOAT" | "STRING" | "BOOLEAN"

  // Each variable has values per mode
  for (const [modeId, value] of Object.entries(variable.valuesByMode)) {
    const modeName = collection.modes.find(m => m.modeId === modeId)?.name;
    console.log(`  ${modeName}: ${JSON.stringify(value)}`);
  }
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
