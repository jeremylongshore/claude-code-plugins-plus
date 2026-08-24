# StackBlitz Skill Pack

> 10 production-ready Claude Code skills for StackBlitz WebContainers -- real browser-based Node.js runtime code.

## What This Is

A practical skill pack for building browser-based development environments with StackBlitz WebContainers. It covers real WebContainer API code including `WebContainer.boot()`, `mount()`, `spawn()`, `fs.readFile()`, jsh shell integration, and StackBlitz SDK embedding.

## Installation

```bash
/plugin install stackblitz-pack@claude-code-plugins-plus
```

## Skills

### Skills (S01-S10)

| # | Skill | What It Does |
|---|-------|-------------|
| S01 | `stackblitz-install-auth` | Install `@webcontainer/api`, configure COOP/COEP headers |
| S02 | `stackblitz-hello-world` | Boot WebContainer, mount files, npm install, start dev server |
| S03 | `stackblitz-local-dev-loop` | Vite dev setup with cross-origin headers, Vitest for file tree |
| S04 | `stackblitz-sdk-patterns` | Singleton boot, FS CRUD, process management, jsh shell, SDK embedding |
| S05 | `stackblitz-core-workflow-a` | Build browser IDE: file tree, Monaco editor, terminal, live preview |
| S06 | `stackblitz-core-workflow-b` | Embed projects from GitHub, inline code, URL-based iframes |
| S07 | `stackblitz-common-errors` | Fix SharedArrayBuffer, COOP/COEP, boot failures, npm install |
| S08 | `stackblitz-debug-bundle` | Diagnose boot state, FS health, Node.js version, browser support |
| S09 | `stackblitz-rate-limits` | Memory limits, FS size, process count, native addon restrictions |
| S10 | `stackblitz-security-basics` | Browser sandbox model, input validation, CSP headers |

## Key Concepts Covered

- **WebContainer.boot()**: Single instance per page, runs Node.js in browser
- **mount()**: Load FileSystemTree into virtual FS (ephemeral, in-memory)
- **spawn()**: Run npm, node, jsh, or any Node.js CLI tool
- **server-ready event**: Detect when spawned server is listening
- **jsh**: Built-in shell for interactive terminal (pairs with xterm.js)
- **COOP/COEP headers**: Required for SharedArrayBuffer (cross-origin isolation)
- **StackBlitz SDK**: Embed interactive editors from GitHub repos or inline code

## License

MIT
