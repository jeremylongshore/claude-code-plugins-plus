# Shipwright (AI Agency)

Describe your app in plain English — Shipwright builds, tests, and deploys it autonomously via a 9-phase pipeline. Powered by `product-agent` on PyPI.

## Quick Start

1. Install the build engine:

```bash
pip install product-agent
```

2. Use the skills:
- `/shipwright-build` — Build a new app from a plain-English description
- `/shipwright-enhance` — Add features to an existing Shipwright project
- `/shipwright-stacks` — List supported tech stacks
- `/shipwright-projects` — List and manage existing Shipwright projects

## Supported Stacks

- **Next.js + Supabase** — Full-stack with auth, database, and edge functions
- **Next.js + Prisma** — Full-stack with type-safe ORM
- **SvelteKit** — Lightweight full-stack with Svelte
- **Astro** — Content-focused static and hybrid sites

## The 9-Phase Pipeline

Shipwright orchestrates a complete build lifecycle:

1. **Intake** — Parse the natural-language app description
2. **Architecture** — Select stack, define schema, plan routes
3. **Scaffold** — Generate project structure and boilerplate
4. **Implement** — Write application code across all layers
5. **Test** — Generate and run test suites (1,627+ tests validated)
6. **Integrate** — Wire up APIs, auth, and data layer
7. **Polish** — Lint, format, accessibility, and performance passes
8. **Validate** — End-to-end verification and build checks
9. **Ship** — Package for deployment

## Build Engine

Shipwright delegates execution to [`product-agent`](https://pypi.org/project/product-agent/), an autonomous build engine available on PyPI. The agent handles code generation, testing, and validation across all supported stacks.

## Files

- Skill: `${CLAUDE_PLUGIN_ROOT}/skills/shipwright-pipeline/SKILL.md`
- Commands: `${CLAUDE_PLUGIN_ROOT}/commands/`

## Links

- [GitHub Repository](https://github.com/Wynelson94/shipwright)
- [product-agent on PyPI](https://pypi.org/project/product-agent/)
