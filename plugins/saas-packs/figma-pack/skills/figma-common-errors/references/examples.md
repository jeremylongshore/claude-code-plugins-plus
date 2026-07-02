# figma-common-errors: Worked Examples

Worked examples for the `figma-common-errors` skill — extracted from the skill's Examples section.

## Error Wrapper with Actionable Messages

```typescript
function diagnoseFigmaError(status: number, body: string): string {
  switch (status) {
    case 403: return 'Auth failed. Check: (1) PAT not expired (2) correct scopes (3) file shared with you';
    case 404: return 'Not found. Check: (1) file key from URL (2) file not deleted (3) node IDs valid';
    case 429: return 'Rate limited. Implement exponential backoff with Retry-After header';
    case 500: return 'Figma server error. Check status.figma.com and retry with backoff';
    default: return `Unexpected ${status}: ${body}`;
  }
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
