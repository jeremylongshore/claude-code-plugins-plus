---
name: aura
description: |
  All-in-one fullstack development skill for Claude Code. Build, fix, clean,
  deploy, review, and more through a single /aura command. 33 modes, 6-layer
  security, 23 hooks, 8 languages, 75% token savings.
  Use when user asks to build, fix, clean, deploy, review, debug, scaffold,
  refactor, test, audit, or automate development workflows.
  Trigger with "aura", "/aura", "build", "fix", "deploy", "review".
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, Agent, WebFetch
version: 6.2.0
author: smorky85 <smorky850612@users.noreply.github.com>
license: MIT
compatible-with: claude-code, cursor, codex
tags: [community, fullstack, security, owasp, hooks, cross-platform]
---

# AuraKit — /aura

> One command to build, fix, review, test, deploy, and secure fullstack apps.

## Modes (33 total)

| Mode | Trigger | What It Does |
|------|---------|-------------|
| BUILD | `/aura build` | Scaffold and generate code |
| FIX | `/aura fix` | Diagnose and fix bugs |
| CLEAN | `/aura clean` | Refactor and organize |
| DEPLOY | `/aura deploy` | Build, test, deploy |
| REVIEW | `/aura review` | Code review with security focus |
| TDD | `/aura tdd` | Test-driven development |
| SECURITY | `/aura security` | OWASP security audit |
| PM | `/aura pm` | Product discovery and planning |
| ... | ... | 25 more modes |

## Security (6 Layers)

1. `.env` guard — blocks commits without `.gitignore` coverage
2. `disallowed-tools` — role-based tool separation
3. `bash-guard.js` — dangerous command blocking
4. `security-scan.js` — secret pattern detection
5. Worktree isolation for agent execution
6. Convention checks (CONV-001 through CONV-005)

## Install

```bash
npm install -g @smorky85/aurakit
```

## Links

- [GitHub](https://github.com/smorky850612/Aurakit)
- [npm](https://www.npmjs.com/package/@smorky85/aurakit)
