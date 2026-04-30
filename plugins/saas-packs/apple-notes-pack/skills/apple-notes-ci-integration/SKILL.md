---
name: apple-notes-ci-integration
description: 'Run Apple Notes automation in CI on macOS runners.

  Trigger: "apple notes CI".

  '
allowed-tools: Read, Write, Edit, Bash(osascript:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- macos
- apple-notes
- automation
compatibility: Designed for Claude Code
---
# Apple Notes CI Integration

## Overview

Apple Notes automation is macOS-only because it depends on the Apple Events subsystem and Notes.app. CI pipelines must use GitHub Actions macOS runners (`macos-latest` or `macos-14`). However, macOS CI runners have restricted TCC (Transparency, Consent, and Control) permissions, which means direct Notes.app automation via `osascript` will fail in CI. The standard pattern is to run unit tests against a mock JXA client in CI, and reserve real Notes.app integration tests for local macOS machines or self-hosted runners with pre-granted automation permissions.

## GitHub Actions Workflow

```yaml
# .github/workflows/notes-ci.yml
name: Notes Automation CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  unit-tests:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "20", cache: "npm" }
      - run: npm ci
      - name: Verify macOS version
        run: sw_vers
      - name: Lint JXA scripts
        run: |
          # Validate JavaScript syntax in all .jxa files
          for f in scripts/*.jxa; do
            node --check "$f" 2>/dev/null || echo "WARN: $f is osascript-only"
          done
      - name: Unit tests (mocked Notes client)
        run: npm test
      - name: Validate JXA templates
        run: |
          # Ensure osascript can parse (but not execute) JXA scripts
          for f in scripts/*.jxa; do
            osascript -l JavaScript -e "$(cat "$f")" 2>&1 | grep -v "Not authorized" || true
          done
```

## Mock Client for CI

```typescript
// tests/mocks/notes-client.mock.ts
export class MockAppleNotesClient {
  private notes: Array<{ id: string; title: string; body: string; folder: string }> = [];

  createNote(title: string, body: string, folder = "Notes"): string {
    const id = `mock-note-${Date.now()}-${Math.random().toString(36).slice(2)}`;
    this.notes.push({ id, title, body, folder });
    return id;
  }

  listNotes() { return [...this.notes]; }
  getNote(id: string) { return this.notes.find(n => n.id === id) || null; }
  searchNotes(q: string) { return this.notes.filter(n => n.title.includes(q) || n.body.includes(q)); }
  deleteNote(id: string) { this.notes = this.notes.filter(n => n.id !== id); }
  getFolders() { return [...new Set(this.notes.map(n => n.folder))]; }
}
```

## Self-Hosted Runner with TCC Pre-Approval

```bash
# On a self-hosted macOS runner, pre-grant automation permissions:
# 1. Open System Settings > Privacy & Security > Automation
# 2. Grant your CI user's terminal access to Notes.app
# 3. Verify with:
osascript -l JavaScript -e 'Application("Notes").defaultAccount.notes.length'

# For headless runners, use tccutil (requires SIP adjustment or MDM profile):
# sudo tccutil --insert com.apple.Notes --service AppleEvents --app /usr/bin/osascript
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| "Not authorized to send Apple events" in CI | TCC blocks automation on CI runners | Use mock client; real tests on self-hosted runner |
| `osascript` syntax errors not caught | JXA has no standalone linter | Use `node --check` for JS syntax; parse-only validation |
| Flaky tests on `macos-latest` | Runner image updates change Notes state | Pin to `macos-14`; always use mocked client |
| Tests pass locally, fail in CI | Different macOS version or missing app | Check `sw_vers` output; ensure Notes.app exists on runner |
| Timeout waiting for Notes.app | App launch delay on cold runner | Add `open -a Notes && sleep 3` before osascript calls |

## Resources

- [GitHub Actions macOS Runners](https://docs.github.com/en/actions/using-github-hosted-runners/using-github-hosted-runners/about-github-hosted-runners#standard-github-hosted-runners-for-public-repositories)
- [Mac Automation Scripting Guide](https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/)
- [TCC Database Reference](https://www.rainforestqa.com/blog/macos-tcc-db-deep-dive)

## Next Steps

For diagnosing CI failures, see `apple-notes-common-errors`. For production deployment of automation scripts, see `apple-notes-deploy-integration`.
