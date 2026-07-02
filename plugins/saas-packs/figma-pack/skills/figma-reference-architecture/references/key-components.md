# Step 3: Key Components

Deep-dive reference for the `figma-reference-architecture` skill — extracted from the 'Step 3: Key Components' step of the workflow.

**Figma Client** (see `figma-sdk-patterns`):

```typescript
// Singleton with retry, rate limit handling, and caching
const client = new FigmaClient(process.env.FIGMA_PAT!);

// All API calls go through the client
const file = await client.getFile(fileKey);           // GET /v1/files/:key
const nodes = await client.getFileNodes(fileKey, ids); // GET /v1/files/:key/nodes
const images = await client.getImages(fileKey, ids);   // GET /v1/images/:key
const comments = await client.getComments(fileKey);    // GET /v1/files/:key/comments
const vars = await client.getLocalVariables(fileKey);  // GET /v1/files/:key/variables/local
```

**Token Extraction Pipeline** (see `figma-core-workflow-a`):

```typescript
// file → styles → nodes → CSS/JSON tokens
export async function extractTokens(fileKey: string): Promise<DesignToken[]> {
  const file = await client.getFile(fileKey);
  const styleNodes = await client.getFileNodes(fileKey, Object.keys(file.styles));
  return parseTokensFromNodes(file.styles, styleNodes);
}
```

**Asset Export Pipeline** (see `figma-core-workflow-b`):

```typescript
// file → find components → render images → download
export async function exportIcons(fileKey: string, frameId: string) {
  const frame = await client.getFileNodes(fileKey, [frameId]);
  const componentIds = findComponents(frame).map(n => n.id);
  const imageUrls = await client.getImages(fileKey, componentIds, { format: 'svg' });
  return downloadAll(imageUrls);
}
```

**Webhook Handler** (see `figma-webhooks-events`):

```typescript
// Verify passcode → route event → process async
export function webhookRouter(event: FigmaWebhookEvent) {
  switch (event.event_type) {
    case 'FILE_UPDATE': return handleFileUpdate(event);
    case 'LIBRARY_PUBLISH': return handleLibraryPublish(event);
    case 'FILE_COMMENT': return handleComment(event);
  }
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
