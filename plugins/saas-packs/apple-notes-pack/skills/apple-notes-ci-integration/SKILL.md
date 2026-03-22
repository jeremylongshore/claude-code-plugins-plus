---
name: apple-notes-ci-integration
description: |
  Run Apple Notes automation in CI on macOS runners.
  Trigger: "apple notes CI".
allowed-tools: Read, Write, Edit, Bash(osascript:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, macos, apple-notes, automation]
compatible-with: claude-code
---

# Apple Notes CI Integration

## Overview
Apple Notes automation requires macOS — use GitHub Actions macOS runners.

## GitHub Actions Workflow
```yaml
name: Notes Automation Tests
on: [push]

jobs:
  test:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "20" }
      - run: npm ci
      - name: Test Notes access
        run: |
          # macOS CI runners have Notes.app but limited permissions
          osascript -l JavaScript -e "typeof Application(\"Notes\")" || echo "Notes not available in CI"
      - name: Run unit tests (mocked)
        run: npm test
```

## Important Limitation
macOS CI runners (GitHub Actions) have restricted Apple Events permissions. Real Notes.app automation tests must run on local macOS machines. Use mocked clients in CI.

```typescript
// tests/mocks/notes-client.mock.ts
export class MockAppleNotesClient {
  private notes: Array<{ id: string; title: string; body: string }> = [];

  createNote(title: string, body: string): string {
    const id = `note-${Date.now()}`;
    this.notes.push({ id, title, body });
    return id;
  }

  listNotes() { return this.notes; }
  searchNotes(q: string) { return this.notes.filter(n => n.title.includes(q)); }
}
```

## Resources

- [Mac Automation Scripting Guide](https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/)
- [JXA Examples](https://jxa-examples.akjems.com/)
