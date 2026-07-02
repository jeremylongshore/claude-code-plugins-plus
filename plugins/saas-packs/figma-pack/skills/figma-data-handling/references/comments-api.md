# Step 1: Comments API

Deep-dive reference for the `figma-data-handling` skill — extracted from the 'Step 1: Comments API' step of the workflow.

```typescript
const PAT = process.env.FIGMA_PAT!;
const FILE_KEY = process.env.FIGMA_FILE_KEY!;

// GET /v1/files/:key/comments -- requires file_comments:read scope
async function getComments(fileKey: string) {
  const res = await fetch(
    `https://api.figma.com/v1/files/${fileKey}/comments`,
    { headers: { 'X-Figma-Token': PAT } }
  );
  const data = await res.json();

  // data.comments is an array of:
  // { id, message, file_key, parent_id, user, client_meta, resolved_at, created_at, order_id }
  return data.comments;
}

// GET with as_md=true to get rich-text comments as markdown
async function getCommentsAsMarkdown(fileKey: string) {
  const res = await fetch(
    `https://api.figma.com/v1/files/${fileKey}/comments?as_md=true`,
    { headers: { 'X-Figma-Token': PAT } }
  );
  return (await res.json()).comments;
}

// POST /v1/files/:key/comments -- requires file_comments:write scope
async function postComment(fileKey: string, message: string, nodeId?: string) {
  const body: any = { message };
  if (nodeId) {
    body.client_meta = { node_id: nodeId };
  }

  const res = await fetch(
    `https://api.figma.com/v1/files/${fileKey}/comments`,
    {
      method: 'POST',
      headers: {
        'X-Figma-Token': PAT,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    }
  );
  return res.json();
}

// POST reactions to a comment -- requires file_comments:write
async function reactToComment(fileKey: string, commentId: string, emoji: string) {
  return fetch(
    `https://api.figma.com/v1/files/${fileKey}/comments/${commentId}/reactions`,
    {
      method: 'POST',
      headers: {
        'X-Figma-Token': PAT,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ emoji }),
    }
  ).then(r => r.json());
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
