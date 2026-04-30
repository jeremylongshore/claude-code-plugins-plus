---
name: shipwright-pipeline
description: Autonomous app builder that converts plain-English descriptions into
  fully built, tested applications. Use when the user wants to build a new app, scaffold
  a project, generate a full-stack application, or create an app from a description.
  Trigger with "build me an app", "create a new app", "shipwright build", "scaffold
  a project", "generate an application".
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(pip:*), Bash(python:*), Bash(npm:*),
  Bash(npx:*), Bash(git:*)
version: 1.0.0
author: Nate Nelson <nate@blacksheephq.ai>
license: MIT
tags:
- ai-agency
- app-builder
- code-generator
- autonomous-agent
compatibility: Designed for Claude Code
---
# Shipwright Pipeline

## Overview

Shipwright converts a plain-English app description into a fully built, tested, and deployment-ready application. It delegates execution to `product-agent`, an autonomous 9-phase build engine available on PyPI.

## Prerequisites

- Python 3.10+ available in PATH.
- `product-agent` installed (`pip install product-agent`).
- Node.js 18+ for JavaScript/TypeScript stacks.

## Supported Stacks

- **Next.js + Supabase** — Full-stack with auth, database, and edge functions
- **Next.js + Prisma** — Full-stack with type-safe ORM
- **SvelteKit** — Lightweight full-stack with Svelte
- **Astro** — Content-focused static and hybrid sites

## Instructions

1. Gather the app description from the user. Ask clarifying questions if the description is vague.
2. Confirm the target stack. If none specified, recommend based on the app type:
   - Data-heavy with auth: Next.js + Supabase
   - API-first with complex models: Next.js + Prisma
   - Lightweight interactive: SvelteKit
   - Content or marketing site: Astro
3. Run `product-agent` with the app description and selected stack.
4. Monitor the 9-phase pipeline: Intake, Architecture, Scaffold, Implement, Test, Integrate, Polish, Validate, Ship.
5. Report results to the user including test summary and any warnings.

## Output

- A complete, buildable project directory with all source code, tests, and configuration.
- A test report summarizing pass/fail counts.
- Build verification output confirming the project compiles and starts.

## Error Handling

- If `product-agent` is not installed, prompt the user to install it with `pip install product-agent`.
- If a phase fails, report the phase name, error message, and suggested fix.
- If the selected stack is not supported, list available stacks and ask the user to choose.

## Examples

**Build a SaaS dashboard:**
```
/shipwright-build Build a real-time analytics dashboard with user auth, team workspaces, and Stripe billing. Use Next.js + Supabase.
```

**Add features to an existing project:**
```
/shipwright-enhance Add dark mode toggle, export-to-CSV on all tables, and email notification preferences.
```

**Scaffold a content site:**
```
/shipwright-build Create a developer documentation site with search, versioned docs, and a blog. Use Astro.
```

## Resources

- [Shipwright on GitHub](https://github.com/Wynelson94/shipwright)
- [product-agent on PyPI](https://pypi.org/project/product-agent/)
- See `${CLAUDE_SKILL_DIR}/references/examples.md` for usage examples.
