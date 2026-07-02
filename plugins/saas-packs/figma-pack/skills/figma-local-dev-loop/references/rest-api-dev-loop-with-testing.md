# Step 4: REST API Dev Loop with Testing

Deep-dive reference for the `figma-local-dev-loop` skill — extracted from the 'Step 4: REST API Dev Loop with Testing' step of the workflow.

```json
{
  "scripts": {
    "dev": "tsx watch src/extract-tokens.ts",
    "test": "vitest",
    "test:watch": "vitest --watch"
  }
}
```

```typescript
// tests/figma-client.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { readFileSync } from 'fs';

// Load a saved API response for offline testing
const sampleFile = JSON.parse(
  readFileSync('tests/fixtures/sample-file.json', 'utf-8')
);

describe('Figma token extraction', () => {
  beforeEach(() => {
    // Mock fetch to return saved fixture
    vi.spyOn(global, 'fetch').mockResolvedValue(
      new Response(JSON.stringify(sampleFile), { status: 200 })
    );
  });

  it('should extract color styles from file', async () => {
    const res = await fetch('https://api.figma.com/v1/files/test-key');
    const file = await res.json();
    const styles = Object.values(file.styles);
    expect(styles.length).toBeGreaterThan(0);
  });
});
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
