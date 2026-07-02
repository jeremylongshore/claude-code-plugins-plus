# Step 1: Typed REST API Client

Deep-dive reference for the `figma-sdk-patterns` skill — extracted from the 'Step 1: Typed REST API Client' step of the workflow.

```typescript
// src/figma-client.ts
export class FigmaClient {
  private baseUrl = 'https://api.figma.com';

  constructor(private token: string) {
    if (!token) throw new Error('Figma token is required');
  }

  private async request<T>(path: string, init?: RequestInit): Promise<T> {
    const res = await fetch(`${this.baseUrl}${path}`, {
      ...init,
      headers: {
        'X-Figma-Token': this.token,
        'Content-Type': 'application/json',
        ...init?.headers,
      },
    });

    if (res.status === 429) {
      const retryAfter = parseInt(res.headers.get('Retry-After') || '60');
      throw new FigmaRateLimitError(retryAfter);
    }
    if (res.status === 403) throw new FigmaAuthError('Invalid or expired token');
    if (res.status === 404) throw new FigmaNotFoundError(path);
    if (!res.ok) throw new FigmaApiError(res.status, await res.text());

    return res.json();
  }

  async getFile(fileKey: string) {
    return this.request<FigmaFileResponse>(`/v1/files/${fileKey}`);
  }

  async getFileNodes(fileKey: string, nodeIds: string[]) {
    const ids = encodeURIComponent(nodeIds.join(','));
    return this.request<FigmaNodesResponse>(`/v1/files/${fileKey}/nodes?ids=${ids}`);
  }

  async getImages(fileKey: string, nodeIds: string[], opts?: ImageOptions) {
    const params = new URLSearchParams({
      ids: nodeIds.join(','),
      format: opts?.format ?? 'png',
      scale: String(opts?.scale ?? 2),
    });
    return this.request<FigmaImagesResponse>(`/v1/images/${fileKey}?${params}`);
  }

  async getComments(fileKey: string) {
    return this.request<FigmaCommentsResponse>(`/v1/files/${fileKey}/comments`);
  }

  async postComment(fileKey: string, message: string, nodeId?: string) {
    return this.request(`/v1/files/${fileKey}/comments`, {
      method: 'POST',
      body: JSON.stringify({
        message,
        ...(nodeId && { client_meta: { node_id: nodeId } }),
      }),
    });
  }

  async getLocalVariables(fileKey: string) {
    return this.request<FigmaVariablesResponse>(
      `/v1/files/${fileKey}/variables/local`
    );
  }
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
