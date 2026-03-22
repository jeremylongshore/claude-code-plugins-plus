---
name: stackblitz-hello-world
description: |
  Boot a WebContainer, mount files, install npm packages, and run a dev server in the browser.
  Use when learning WebContainers, building browser-based IDEs,
  or running Node.js without a backend server.
  Trigger: "stackblitz hello world", "webcontainer example", "run node in browser".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ide, webcontainers, stackblitz]
compatible-with: claude-code
---

# StackBlitz Hello World

## Overview

Boot a WebContainer, mount a file system tree, install dependencies with npm, and start a dev server -- all running inside the browser tab. No backend server needed.

## Prerequisites

- `@webcontainer/api` installed (see `stackblitz-install-auth`)
- Cross-origin isolation headers configured
- Modern browser (Chrome 90+, Firefox 90+, Safari 16.4+)

## Instructions

### Step 1: Define File System Tree

```typescript
import { WebContainer, FileSystemTree } from '@webcontainer/api';

const files: FileSystemTree = {
  'package.json': {
    file: {
      contents: JSON.stringify({
        name: 'wc-hello',
        scripts: { start: 'node index.js', dev: 'nodemon index.js' },
        dependencies: { express: '^4.18.0' },
      }),
    },
  },
  'index.js': {
    file: {
      contents: `
const express = require('express');
const app = express();
app.get('/', (req, res) => res.send('Hello from WebContainer!'));
app.listen(3000, () => console.log('Server running on port 3000'));
      `.trim(),
    },
  },
  src: {
    directory: {
      'utils.js': { file: { contents: 'module.exports = { greet: (n) => "Hello " + n };' } },
    },
  },
};
```

### Step 2: Boot and Mount

```typescript
const wc = await WebContainer.boot();
await wc.mount(files);

console.log('Files mounted. Installing dependencies...');
```

### Step 3: Install Dependencies

```typescript
const installProcess = await wc.spawn('npm', ['install']);

// Stream install output
installProcess.output.pipeTo(new WritableStream({
  write(data) { console.log(data); },
}));

const installCode = await installProcess.exit;
if (installCode !== 0) throw new Error(`npm install failed: exit ${installCode}`);
console.log('Dependencies installed.');
```

### Step 4: Start Dev Server

```typescript
const serverProcess = await wc.spawn('npm', ['start']);

serverProcess.output.pipeTo(new WritableStream({
  write(data) { console.log(data); },
}));

// Listen for server-ready event
wc.on('server-ready', (port, url) => {
  console.log(`Server ready at ${url} (port ${port})`);
  // Display in iframe
  document.querySelector('iframe')!.src = url;
});
```

## Output

```
added 57 packages in 3s
Dependencies installed.
Server running on port 3000
Server ready at https://xxx.webcontainer.io (port 3000)
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `npm install` hangs | Large dependency tree | Use `--prefer-offline` or fewer deps |
| `server-ready` never fires | App not listening on a port | Ensure `app.listen()` is called |
| Port conflict | Another process on same port | Use a different port |
| `ENOENT` for file | File not in mount tree | Verify FileSystemTree structure |

## Resources

- [WebContainer Quickstart](https://webcontainers.io/guides/quickstart)
- [FileSystemTree API](https://webcontainers.io/api#filesystemtree)
- [WebContainer Tutorial](https://webcontainers.io/tutorial/2-setting-up-webcontainers)

## Next Steps

Proceed to `stackblitz-local-dev-loop` for development workflow setup.
