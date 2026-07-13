# Step 3: Immediate Mitigation

Deep-dive reference for the `figma-incident-runbook` skill — extracted from the 'Step 3: Immediate Mitigation' step of the workflow.

**For 403 (Token Expired):**

```bash
# Generate new PAT in Figma Settings > Personal access tokens
# Then update your deployment:

# GitHub Actions
gh secret set FIGMA_PAT --body "figd_new-token-here"

# Cloud Run
echo -n "figd_new-token" | gcloud secrets versions add figma-pat --data-file=-
gcloud run services update my-service --update-secrets="FIGMA_PAT=figma-pat:latest"

# Fly.io
fly secrets set FIGMA_PAT=figd_new-token
```

**For 429 (Rate Limited):**

```typescript
// Emergency: disable non-critical Figma calls
const EMERGENCY_MODE = process.env.FIGMA_EMERGENCY === 'true';

async function safeFigmaCall<T>(
  path: string,
  critical: boolean = false
): Promise<T | null> {
  if (EMERGENCY_MODE && !critical) {
    console.warn(`Figma call skipped (emergency mode): ${path}`);
    return null;
  }
  return figmaFetch(path);
}
```

**For 500/503 (Figma Down):**

```typescript
// Serve cached data when Figma is unavailable
async function getTokensWithFallback() {
  try {
    return await extractTokensFromFigma();
  } catch (error) {
    console.warn('Figma unavailable, serving cached tokens');
    // Return last-known-good tokens from cache or file
    const cached = await readFile('output/tokens.json', 'utf-8');
    return JSON.parse(cached);
  }
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
