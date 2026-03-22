# StackBlitz Skill Pack

> 18 production-ready Claude Code skills for StackBlitz WebContainers -- real browser-based Node.js runtime code.

## What This Is

A complete skill pack for building browser-based development environments with StackBlitz WebContainers. Every skill contains real WebContainer API code: `WebContainer.boot()`, `mount()`, `spawn()`, `fs.readFile()`, jsh shell integration, and StackBlitz SDK embedding. No placeholder imports, no fake patterns.

## Installation

```bash
/plugin install stackblitz-pack@claude-code-plugins-plus
```

## Skills

### Standard Skills (S01-S12)

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
| S11 | `stackblitz-prod-checklist` | Headers, browser support matrix, fallback strategies |
| S12 | `stackblitz-upgrade-migration` | WebContainer API version changes, SDK updates |

### Pro Skills (P13-P18)

| # | Skill | What It Does |
|---|-------|-------------|
| P13 | `stackblitz-ci-integration` | Playwright tests for WebContainer apps in CI |
| P14 | `stackblitz-deploy-integration` | Deploy to Vercel/Netlify with proper COOP/COEP headers |
| P15 | `stackblitz-webhooks-events` | WebContainer lifecycle events: server-ready, port, error |
| P16 | `stackblitz-performance-tuning` | Optimize boot time, mount size, process spawning |
| P17 | `stackblitz-cost-tuning` | Free tier vs commercial licensing for WebContainer API |
| P18 | `stackblitz-reference-architecture` | Browser IDE architecture: editor + terminal + preview + FS |

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
