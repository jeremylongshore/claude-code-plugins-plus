---
name: managing-snapshot-tests
description: |
  Create and validate component snapshots for UI regression testing.
  Use when performing specialized testing.
  Trigger with phrases like "update snapshots", "test UI snapshots", or "validate component snapshots".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(test:snapshot-*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# Snapshot Test Manager

## Overview

Create, update, and maintain snapshot tests for UI components and data structures using Jest, Vitest, or pytest snapshot plugins. Manages serialized output snapshots (HTML, JSON, component trees) to detect unexpected changes in rendered output. Handles snapshot lifecycle including creation, review, update, and cleanup of obsolete snapshots.

## Prerequisites

- Jest or Vitest with built-in snapshot support, or `pytest-snapshot`/`syrupy` for Python
- React Testing Library, Vue Test Utils, or equivalent for component rendering
- Snapshot files committed to version control (`.snap` files or `__snapshots__/` directory)
- Component library with stable prop interfaces
- Code review process that includes snapshot diff review

## Instructions

1. Identify components and data structures suitable for snapshot testing:
   - UI components with complex rendered output (navigation bars, forms, cards).
   - API response transformers producing structured JSON.
   - Configuration generators outputting YAML or TOML.
   - Avoid snapshots for highly dynamic content (timestamps, random IDs).
2. Write snapshot tests for each target:
   - Render the component with representative props.
   - Call `expect(result).toMatchSnapshot()` or `toMatchInlineSnapshot()`.
   - Create separate snapshots for each meaningful prop combination.
   - Use inline snapshots for small outputs (under 20 lines) for better readability.
3. Organize snapshot files:
   - Group snapshots by component in `__snapshots__/ComponentName.test.ts.snap`.
   - Name each snapshot descriptively: `"renders with error state"`, `"displays loading skeleton"`.
   - Keep snapshot files in the same directory as the test file.
4. Review and update snapshots when intentional changes occur:
   - Run `jest --updateSnapshot` or `vitest --update` after verifying changes are correct.
   - Review every line of the snapshot diff in pull requests -- do not blindly update.
   - Add a comment in the PR explaining why snapshots changed.
5. Clean up obsolete snapshots:
   - Run `jest --ci` to detect obsolete snapshots that no longer match any test.
   - Delete orphaned `.snap` files for removed components.
   - Periodically run snapshot cleanup to prevent stale data.
6. Set up CI to fail on snapshot mismatches without auto-updating:
   - Use `--ci` flag which treats missing snapshots as failures.
   - Upload snapshot diff output as a CI artifact for review.
7. Consider property-based snapshot alternatives for large components:
   - Use `toMatchObject` for partial structure matching.
   - Use custom serializers to exclude volatile fields.

## Output

- Snapshot test files (`*.test.ts` or `*.test.tsx`) with `toMatchSnapshot()` assertions
- Snapshot data files (`__snapshots__/*.snap`)
- Snapshot update report listing changed, added, and removed snapshots
- CI configuration preventing accidental snapshot updates in automated runs
- Custom serializer modules for filtering dynamic content

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| Snapshot mismatch on unrelated change | Component depends on a shared style or context provider | Isolate components with wrapper providers; mock global styles |
| Snapshot file is enormous (>1000 lines) | Entire page DOM serialized instead of target component | Narrow the snapshot scope to the specific component subtree; use `container.querySelector` |
| Obsolete snapshot warning | Test was renamed or deleted but `.snap` file remains | Run `jest --updateSnapshot` to remove orphaned entries; delete unused `.snap` files |
| Snapshot differs between local and CI | Different Node.js version or OS renders slightly different output | Pin Node.js version in CI; use `toMatchInlineSnapshot` for exact control |
| Non-deterministic snapshot | Component includes random keys, timestamps, or Math.random() | Mock `Date.now()` and `Math.random()`; use `expect.any(String)` for volatile fields |

## Examples

**React component snapshot test (Jest):**
```tsx
import { render } from '@testing-library/react';
import { Alert } from './Alert';

describe('Alert', () => {
  it('renders success variant', () => {
    const { container } = render(
      <Alert variant="success" message="Operation completed" />
    );
    expect(container.firstChild).toMatchSnapshot();
  });

  it('renders error with inline snapshot', () => {
    const { container } = render(
      <Alert variant="error" message="Something failed" />
    );
    expect(container.firstChild).toMatchInlineSnapshot(`
      <div class="alert alert-error" role="alert">
        <span>Something failed</span>
      </div>
    `);
  });
});
```

**Custom serializer to exclude dynamic IDs:**
```typescript
// jest.config.ts
export default {
  snapshotSerializers: ['./test/serializers/strip-ids.ts'],
};

// test/serializers/strip-ids.ts
export const serialize = (val: string) =>
  val.replace(/id="[a-z0-9-]+"/g, 'id="[dynamic]"');
export const test = (val: unknown) => typeof val === 'string' && val.includes('id=');
```

## Resources

- Jest snapshot testing: https://jestjs.io/docs/snapshot-testing
- Vitest snapshots: https://vitest.dev/guide/snapshot
- React Testing Library: https://testing-library.com/docs/react-testing-library/intro/
- Syrupy (pytest snapshots): https://github.com/toptal/syrupy
- Effective Snapshot Testing: https://kentcdodds.com/blog/effective-snapshot-testing
