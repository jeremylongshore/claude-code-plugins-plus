---
name: evernote-upgrade-migration
description: |
  Upgrade Evernote SDK versions and migrate between API versions.
  Use when upgrading SDK, handling breaking changes,
  or migrating to newer API patterns.
  Trigger with phrases like "upgrade evernote sdk", "evernote migration",
  "update evernote", "evernote breaking changes".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Evernote Upgrade & Migration

## Current State
!`npm list evernote 2>/dev/null || echo 'evernote SDK not installed'`

## Overview
Guide for upgrading Evernote SDK versions, converting callback-based code to Promises, handling breaking changes, and maintaining backward compatibility during gradual migration.

## Prerequisites
- Existing Evernote integration to upgrade
- Test environment for validation
- Understanding of current implementation patterns

## Instructions

### Step 1: Check Current Version

Identify your current SDK version and compare against the latest release. Check the changelog for breaking changes between versions.

```bash
# Check installed version
npm list evernote

# Check latest available
npm view evernote version

# View changelog
npm view evernote repository.url
```

### Step 2: Review Breaking Changes

Common breaking changes across Evernote SDK versions:
- **Constructor changes**: `new Evernote.Note()` became `new Evernote.Types.Note()`
- **Callback to Promise**: Older versions used callbacks, newer versions return Promises
- **Import path changes**: Module structure may change between major versions
- **Thrift version updates**: Underlying Thrift protocol may change serialization

### Step 3: Convert Callbacks to Promises

Wrap callback-based SDK calls in Promise wrappers for modern async/await usage.

```javascript
// OLD: Callback pattern
noteStore.getNote(guid, true, false, false, false, (error, note) => {
  if (error) return handleError(error);
  processNote(note);
});

// NEW: Promise/async pattern
const note = await noteStore.getNote(guid, true, false, false, false);
processNote(note);
```

### Step 4: Compatibility Layer

Build a compatibility layer that supports both old and new SDK patterns during gradual migration. This allows upgrading module by module instead of a big-bang rewrite.

```javascript
class EvernoteCompat {
  constructor(noteStore) {
    this.noteStore = noteStore;
  }

  // Works with both callback and Promise-based SDK
  async getNote(guid, opts = {}) {
    const { withContent = true, withResources = false } = opts;
    return this.noteStore.getNote(guid, withContent, withResources, false, false);
  }

  async createNote(title, content, notebookGuid) {
    const Note = Evernote.Types?.Note || Evernote.Note;
    const note = new Note();
    note.title = title;
    note.content = content;
    if (notebookGuid) note.notebookGuid = notebookGuid;
    return this.noteStore.createNote(note);
  }
}
```

### Step 5: Test Suite Updates

Update test assertions for new SDK response shapes. Add tests for the compatibility layer. Run both unit and integration tests against the sandbox.

### Step 6: Deprecation Warnings

Add deprecation warnings to old patterns so team members know to use new patterns. Remove after migration is complete.

For the full migration script, compatibility layer, test suite updates, and deprecation system, see [Implementation Guide](references/implementation-guide.md).

## Output
- SDK version comparison and changelog review
- Callback-to-Promise conversion patterns
- `EvernoteCompat` compatibility layer for gradual migration
- Updated test suite for new SDK behavior
- Deprecation warning system for old patterns

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `Evernote.Note is not a constructor` | Old import style after upgrade | Use `Evernote.Types.Note` |
| `callback is not a function` | Mixed callback/Promise patterns | Use Promise consistently, remove callback arg |
| `Cannot read property 'then'` | Using old callback-only method | Update to Promise-based SDK method |
| Type mismatch | Thrift serialization change | Re-generate types from updated Thrift definitions |

## Resources
- [Evernote SDK JS](https://github.com/Evernote/evernote-sdk-js)
- [SDK Releases](https://github.com/Evernote/evernote-sdk-js/releases)
- [Python SDK](https://github.com/Evernote/evernote-sdk-python)
- [API Reference](https://dev.evernote.com/doc/reference/)

## Next Steps
For CI/CD integration, see `evernote-ci-integration`.

## Examples

**Gradual migration**: Wrap existing NoteStore with `EvernoteCompat`, upgrade SDK version, update modules one at a time to use the new patterns, and remove the compatibility layer when migration is complete.

**Callback to async/await**: Find all callback-based Evernote API calls using `grep -r 'noteStore.*function.*error'`, convert each to async/await, and update error handling from `if (error)` to `try/catch`.
