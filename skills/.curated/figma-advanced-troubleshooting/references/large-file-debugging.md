# Step 4: Large File Debugging

Deep-dive reference for the `figma-advanced-troubleshooting` skill — extracted from the 'Step 4: Large File Debugging' step of the workflow.

```typescript
// Large Figma files (1000+ components) can cause:
// - Response timeouts (>30s)
// - Memory issues (100+ MB JSON)
// - Rate limits from repeated retries

// Strategy: chunk the file by page
async function fetchLargeFileSafely(fileKey: string, token: string) {
  // 1. Get file metadata with depth=1 (just pages, not children)
  const meta = await fetch(
    `https://api.figma.com/v1/files/${fileKey}?depth=1`,
    { headers: { 'X-Figma-Token': token } }
  ).then(r => r.json());

  console.log(`File: ${meta.name}, Pages: ${meta.document.children.length}`);

  // 2. Fetch each page's content individually
  const results = [];
  for (const page of meta.document.children) {
    console.log(`Fetching page: ${page.name} (${page.id})`);

    const pageData = await fetch(
      `https://api.figma.com/v1/files/${fileKey}/nodes?ids=${page.id}`,
      { headers: { 'X-Figma-Token': token } }
    ).then(r => r.json());

    results.push({ pageId: page.id, pageName: page.name, data: pageData });

    // Respect rate limits between page fetches
    await new Promise(r => setTimeout(r, 500));
  }

  return results;
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
