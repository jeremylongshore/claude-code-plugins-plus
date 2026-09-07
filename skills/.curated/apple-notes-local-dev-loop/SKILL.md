---
name: apple-notes-local-dev-loop
description: 'Set up local development workflow for Apple Notes automation with JXA
  hot reload.

  Trigger: "apple notes dev loop".

  '
allowed-tools: Read, Write, Edit, Bash(osascript:*), Grep
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- macos
- apple-notes
- automation
compatibility: Designed for Claude Code
---
# Apple Notes Local Dev Loop

## Overview

Iterative development workflow for Apple Notes JXA scripts with file watching and test helpers.

## Prerequisites

- A local macOS development machine and a test-only `On My Mac` folder, or a fully mocked Notes adapter.
- Synthetic test fixtures with no production note content, account names, or credentials.
- A source-controlled allowlist of scripts eligible for local execution.

## Instructions

### Step 1: Project Setup

```bash
mkdir apple-notes-automation && cd apple-notes-automation
npm init -y
npm install -D chokidar tsx typescript
```

### Step 2: JXA Runner with Hot Reload

```typescript
// src/dev/watch-runner.ts
import { watch } from "chokidar";
import { execSync } from "child_process";

watch("scripts/*.js", { ignoreInitial: true }).on("change", (path) => {
  console.log(`Changed: ${path} — running...`);
  try {
    const output = execSync(`osascript -l JavaScript "${path}"`, { encoding: "utf8" });
    console.log(output);
  } catch (err: any) {
    console.error(err.stderr);
  }
});

console.log("Watching scripts/*.js for changes...");
```

### Step 3: Test Helper

```typescript
// src/dev/test-notes.ts
import { execSync } from "child_process";

function runJxa(script: string): string {
  return execSync(`osascript -l JavaScript -e '${script}'`, { encoding: "utf8" }).trim();
}

function getNoteCount(): number {
  return parseInt(runJxa("Application(\"Notes\").defaultAccount.notes.length"));
}

function createTestNote(title: string): string {
  return runJxa(`
    const Notes = Application("Notes");
    const note = Notes.Note({name: "${title}", body: "<p>Test</p>"});
    Notes.defaultAccount.folders[0].notes.push(note);
    note.id();
  `);
}

export { runJxa, getNoteCount, createTestNote };
```

### Step 4: Dev Scripts

```json
{
  "scripts": {
    "dev": "tsx src/dev/watch-runner.ts",
    "test:notes": "tsx src/dev/test-notes.ts"
  }
}
```

## Output

- Hot-reload JXA development with file watching
- Test helpers for note CRUD operations
- Iterative script development workflow

## Error Handling

Stop the watcher when a script fails and surface only the exit status plus a redacted error category. Never hot-run an edited script against a production or synchronized default account. If a test mutation is required, use the designated test folder and reconcile it before the next run.

## Examples

Run unit tests against a mock client while editing. When a JXA smoke test is necessary, point it at the designated local test folder with a synthetic title, verify the resulting opaque identifier, and clean it up under a test fixture lifecycle—do not run the watcher against `defaultAccount`.

## Resources

- [Mac Automation Scripting Guide](https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/)
- JXA Examples
