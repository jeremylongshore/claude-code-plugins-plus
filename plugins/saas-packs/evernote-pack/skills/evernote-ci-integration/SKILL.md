---
name: evernote-ci-integration
description: |
  Configure CI/CD pipelines for Evernote integrations.
  Use when setting up automated testing, continuous integration,
  or deployment pipelines for Evernote projects.
  Trigger with phrases like "evernote ci", "evernote github actions",
  "evernote pipeline", "automate evernote tests".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Evernote CI Integration

## Overview
Configure continuous integration pipelines for Evernote integrations with mock-based unit tests, sandbox-based integration tests, credential management, and deployment workflows.

## Prerequisites
- Git repository with Evernote integration code
- CI/CD platform (GitHub Actions, GitLab CI, etc.)
- Test framework (Jest, Vitest, or Mocha)
- Sandbox API credentials for integration tests

## Instructions

### Step 1: GitHub Actions Workflow

Create a workflow that runs unit tests on every PR and integration tests on merges to main. Store sandbox credentials as GitHub Actions secrets.

```yaml
# .github/workflows/evernote-ci.yml
name: Evernote CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: npm ci
      - run: npm test
      - name: Integration tests
        if: github.ref == 'refs/heads/main'
        env:
          EVERNOTE_DEV_TOKEN: ${{ secrets.EVERNOTE_SANDBOX_TOKEN }}
          EVERNOTE_SANDBOX: 'true'
        run: npm run test:integration
```

### Step 2: Mock Evernote Client for Unit Tests

Create a mock NoteStore that returns predictable data without hitting the API. Mock `createNote`, `getNote`, `findNotesMetadata`, `listNotebooks`, and `listTags`.

```javascript
class MockNoteStore {
  constructor() {
    this.notes = new Map();
    this.notebooks = [{ guid: 'nb-1', name: 'Default', defaultNotebook: true }];
  }

  async createNote(note) {
    const guid = `note-${Date.now()}`;
    const created = { ...note, guid, created: Date.now(), updated: Date.now() };
    this.notes.set(guid, created);
    return created;
  }

  async getNote(guid, withContent) {
    const note = this.notes.get(guid);
    if (!note) throw { identifier: 'Note.guid', key: guid };
    return withContent ? note : { ...note, content: undefined };
  }

  async listNotebooks() { return this.notebooks; }
}
```

### Step 3: Unit and Integration Test Examples

Write unit tests against the mock client (fast, no credentials needed). Write integration tests against the sandbox (slow, needs `EVERNOTE_DEV_TOKEN`). Tag integration tests so they can run separately.

### Step 4: Secrets Management

Store `EVERNOTE_CONSUMER_KEY`, `EVERNOTE_CONSUMER_SECRET`, and `EVERNOTE_DEV_TOKEN` as repository secrets. Never log or echo secret values. Use environment-specific secret names for staging vs production.

For the full CI workflow, mock client, test examples, and deployment pipeline, see [Implementation Guide](references/implementation-guide.md).

## Output
- GitHub Actions workflow with unit and integration test stages
- `MockNoteStore` class for deterministic unit testing
- Integration test suite using sandbox credentials
- Secrets management configuration for GitHub Actions
- npm scripts: `test`, `test:unit`, `test:integration`

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Integration test auth failure | Expired sandbox token | Regenerate Developer Token in sandbox settings |
| Flaky integration tests | Rate limits in CI | Add delays between integration tests, reduce parallelism |
| Secret not available | Missing repository secret | Add secret in GitHub Settings > Secrets and variables |
| Mock drift | Mock doesn't match real API behavior | Update mock when upgrading SDK version |

## Resources
- [GitHub Actions](https://docs.github.com/en/actions)
- [Jest Documentation](https://jestjs.io/docs/getting-started)
- [Evernote Sandbox](https://sandbox.evernote.com)
- [GitHub Encrypted Secrets](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions)

## Next Steps
For deployment pipelines, see `evernote-deploy-integration`.

## Examples

**Unit test suite**: Test `NoteService.createNote()` against `MockNoteStore` to verify ENML wrapping, title sanitization, and tag handling without any API calls.

**Sandbox integration test**: In CI, create a note in the sandbox, retrieve it by GUID, verify content matches, then delete it. Runs only on main branch merges.
