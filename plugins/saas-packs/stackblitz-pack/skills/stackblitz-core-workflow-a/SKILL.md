---
name: stackblitz-core-workflow-a
description: |
  Build a browser-based code editor with WebContainers: file tree, editor, terminal, and preview.
  Use when creating interactive coding environments, building educational tools,
  or embedding development environments in web apps.
  Trigger: "webcontainer IDE", "browser IDE", "stackblitz editor", "code playground".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ide, webcontainers, stackblitz]
compatible-with: claude-code
---

# StackBlitz Core Workflow A: Browser IDE

## Overview

Build a complete browser-based IDE using WebContainers: file explorer, code editor (Monaco/CodeMirror), integrated terminal (xterm.js + jsh), and live preview iframe. This is the architecture behind bolt.new.

## Instructions

### Step 1: HTML Layout

```html
<div id="app">
  <div id="file-tree"></div>
  <div id="editor"></div>
  <div id="terminal"></div>
  <iframe id="preview"></iframe>
</div>
```

### Step 2: Boot and Mount Project

```typescript
import { WebContainer, FileSystemTree } from '@webcontainer/api';

const files: FileSystemTree = {
  'package.json': {
    file: { contents: JSON.stringify({
      name: 'playground', type: 'module',
      scripts: { dev: 'vite' },
      dependencies: { vite: '^5.0.0' },
    }) },
  },
  'index.html': {
    file: { contents: '<!DOCTYPE html><html><body><div id="app"></div><script type="module" src="/src/main.js"></script></body></html>' },
  },
  src: { directory: {
    'main.js': { file: { contents: 'document.getElementById("app").innerHTML = "<h1>Hello!</h1>";' } },
  }},
};

const wc = await WebContainer.boot();
await wc.mount(files);
```

### Step 3: File Tree with Live Updates

```typescript
async function renderFileTree(path = '/') {
  const entries = await wc.fs.readdir(path, { withFileTypes: true });
  const tree = document.getElementById('file-tree')!;

  for (const entry of entries) {
    if (entry.name === 'node_modules') continue;
    const fullPath = `${path}${path === '/' ? '' : '/'}${entry.name}`;
    const el = document.createElement('div');
    el.textContent = entry.isDirectory() ? `📁 ${entry.name}` : `📄 ${entry.name}`;
    el.onclick = async () => {
      if (!entry.isDirectory()) {
        const content = await wc.fs.readFile(fullPath, 'utf-8');
        editor.setValue(content); // Monaco editor
        currentFile = fullPath;
      }
    };
    tree.appendChild(el);
  }
}
```

### Step 4: Save Editor Changes to WebContainer

```typescript
let currentFile = '/src/main.js';

// Monaco editor onChange
editor.onDidChangeModelContent(async () => {
  const content = editor.getValue();
  await wc.fs.writeFile(currentFile, content);
  // Vite HMR will auto-reload the preview
});
```

### Step 5: Terminal + Preview

```typescript
// Terminal
const jsh = await wc.spawn('jsh', { terminal: { cols: 80, rows: 12 } });
jsh.output.pipeTo(new WritableStream({
  write(data) { terminal.write(data); },
}));

// Install and start dev server
const install = await wc.spawn('npm', ['install']);
await install.exit;
await wc.spawn('npm', ['run', 'dev']);

// Preview iframe
wc.on('server-ready', (port, url) => {
  document.getElementById('preview')!.src = url;
});
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Preview blank | Server not ready yet | Wait for `server-ready` event |
| HMR not working | Vite not running | Check npm install succeeded |
| File tree empty | Mount failed | Verify FileSystemTree structure |

## Resources

- [WebContainer Tutorial](https://webcontainers.io/tutorial/2-setting-up-webcontainers)
- [bolt.new Source](https://github.com/stackblitz/bolt.new)
- [Add Interactivity](https://webcontainers.io/tutorial/7-add-interactivity)

## Next Steps

For embedding and sharing projects, see `stackblitz-core-workflow-b`.
