# Step 2: Version History API

Deep-dive reference for the `figma-data-handling` skill — extracted from the 'Step 2: Version History API' step of the workflow.

```typescript
// GET /v1/files/:key/versions -- requires file_versions:read scope
async function getVersionHistory(fileKey: string) {
  const res = await fetch(
    `https://api.figma.com/v1/files/${fileKey}/versions`,
    { headers: { 'X-Figma-Token': PAT } }
  );
  const data = await res.json();

  // data.versions: array of { id, created_at, label, description, user }
  // Ordered by created_at (most recent first)
  return data.versions;
}

// Paginate through all versions
async function getAllVersions(fileKey: string) {
  const versions: any[] = [];
  let url: string | null = `https://api.figma.com/v1/files/${fileKey}/versions`;

  while (url) {
    const res = await fetch(url, { headers: { 'X-Figma-Token': PAT } });
    const data = await res.json();
    versions.push(...data.versions);

    // Pagination uses cursor-based pagination
    url = data.pagination?.next_page
      ? `https://api.figma.com/v1/files/${fileKey}/versions?before=${data.pagination.next_page}`
      : null;
  }

  return versions;
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
