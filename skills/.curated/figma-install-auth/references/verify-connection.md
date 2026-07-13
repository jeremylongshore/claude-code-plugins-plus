# Step 3: Verify Connection

Deep-dive reference for the `figma-install-auth` skill — extracted from the 'Step 3: Verify Connection' step of the workflow.

```bash
# Test with curl -- should return your user profile
curl -s -H "X-Figma-Token: ${FIGMA_PAT}" \
  https://api.figma.com/v1/me | jq '.handle, .email'
```

```typescript
// verify-figma.ts
const PAT = process.env.FIGMA_PAT!;

const res = await fetch('https://api.figma.com/v1/me', {
  headers: { 'X-Figma-Token': PAT },
});

if (!res.ok) throw new Error(`Figma auth failed: ${res.status}`);
const me = await res.json();
console.log(`Authenticated as ${me.handle} (${me.email})`);
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
