# Step 4: Variables API (Enterprise Only)

Deep-dive reference for the `figma-enterprise-rbac` skill — extracted from the 'Step 4: Variables API (Enterprise Only)' step of the workflow.

```typescript
// GET /v1/files/:key/variables/local -- Tier 2, requires file_variables:read
async function getLocalVariables(fileKey: string, token: string) {
  const res = await fetch(
    `https://api.figma.com/v1/files/${fileKey}/variables/local`,
    { headers: { Authorization: `Bearer ${token}` } }
  );
  if (res.status === 403) {
    throw new Error('Variables API requires Figma Enterprise plan');
  }
  return res.json();
  // { meta: { variables: Record<id, Variable>, variableCollections: Record<id, Collection> } }
}

// GET /v1/files/:key/variables/published -- published variables
async function getPublishedVariables(fileKey: string, token: string) {
  const res = await fetch(
    `https://api.figma.com/v1/files/${fileKey}/variables/published`,
    { headers: { Authorization: `Bearer ${token}` } }
  );
  return res.json();
  // Published variables have a subscribed_id that changes each publish
}

// POST /v1/files/:key/variables -- bulk create/update/delete
async function updateVariables(
  fileKey: string,
  changes: VariableChanges,
  token: string
) {
  const res = await fetch(
    `https://api.figma.com/v1/files/${fileKey}/variables`,
    {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(changes),
    }
  );
  return res.json();
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
