---
name: stackblitz-sdk-patterns
description: |
  Production patterns for WebContainer API: file system operations, process management, and jsh shell.
  Use when building browser IDEs, managing WebContainer lifecycle,
  or implementing terminal emulation with jsh.
  Trigger: "webcontainer patterns", "stackblitz best practices", "webcontainer file system".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ide, webcontainers, stackblitz]
compatible-with: claude-code
---

# StackBlitz SDK Patterns

## Overview

Production patterns for the WebContainer API: singleton boot, file system CRUD, process spawning and management, jsh interactive shell, and the StackBlitz SDK for embedding projects.

## Instructions

### Step 1: Singleton WebContainer Instance

```typescript
import { WebContainer } from '@webcontainer/api';

let instance: WebContainer | null = null;

export async function getWebContainer(): Promise<WebContainer> {
  if (!instance) {
    instance = await WebContainer.boot();
  }
  return instance;
}

// Teardown
export async function teardownWebContainer() {
  if (instance) {
    instance.teardown();
    instance = null;
  }
}
```

### Step 2: File System Operations

```typescript
const wc = await getWebContainer();

// Write file
await wc.fs.writeFile('/src/app.ts', 'export const hello = "world";');

// Read file
const content = await wc.fs.readFile('/src/app.ts', 'utf-8');

// Read directory
const entries = await wc.fs.readdir('/src', { withFileTypes: true });
entries.forEach(entry => {
  console.log(`${entry.name} (${entry.isDirectory() ? 'dir' : 'file'})`);
});

// Create directory
await wc.fs.mkdir('/src/components', { recursive: true });

// Delete file
await wc.fs.rm('/src/old.ts');

// Delete directory
await wc.fs.rm('/dist', { recursive: true });

// Watch for changes
wc.fs.watch('/src', { recursive: true }, (event, filename) => {
  console.log(`${event}: ${filename}`);
});
```

### Step 3: Process Management

```typescript
// Spawn a process
const proc = await wc.spawn('node', ['script.js']);

// Stream stdout
const reader = proc.output.getReader();
while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  console.log(value);
}

// Write to stdin
const writer = proc.input.getWriter();
await writer.write('user input\n');
await writer.close();

// Wait for exit
const exitCode = await proc.exit;

// Kill a process
proc.kill();
```

### Step 4: jsh Interactive Shell

```typescript
// jsh is WebContainer's built-in shell
const jshProcess = await wc.spawn('jsh', {
  terminal: { cols: 80, rows: 24 },
});

// Connect to xterm.js
import { Terminal } from 'xterm';
const terminal = new Terminal();
terminal.open(document.getElementById('terminal')!);

jshProcess.output.pipeTo(new WritableStream({
  write(data) { terminal.write(data); },
}));

terminal.onData((data) => {
  const writer = jshProcess.input.getWriter();
  writer.write(data);
  writer.releaseLock();
});
```

### Step 5: StackBlitz SDK (Embedding)

```typescript
import sdk from '@stackblitz/sdk';

// Embed an existing project
sdk.embedProjectId('container', 'vitejs-vite-template', {
  height: 500,
  openFile: 'src/App.tsx',
  terminalHeight: 30,
});

// Embed from GitHub
sdk.embedGithubProject('container', 'user/repo', {
  openFile: 'README.md',
});

// Create new project programmatically
sdk.embedProject('container', {
  title: 'My Project',
  template: 'node',
  files: {
    'index.js': 'console.log("Hello!")',
    'package.json': '{"name":"demo","scripts":{"start":"node index.js"}}',
  },
});
```

## Error Handling

| Pattern | Use Case | Benefit |
|---------|----------|---------|
| Singleton boot | Multiple components need WC | Only one instance allowed per page |
| Process kill on teardown | Page navigation | Prevents orphaned processes |
| fs.watch | Live preview | Auto-rebuild on file changes |
| jsh + xterm.js | Terminal emulator | Full shell experience in browser |

## Resources

- [WebContainer API Reference](https://webcontainers.io/api)
- [File System Guide](https://webcontainers.io/guides/working-with-the-file-system)
- [StackBlitz SDK Reference](https://developer.stackblitz.com/platform/api/javascript-sdk)

## Next Steps

Apply patterns in `stackblitz-core-workflow-a`.
