# Contributing to pr-to-prompt

Thanks for your interest in contributing!

## Getting Started

```bash
git clone https://github.com/jeremylongshore/pr-to-prompt.git
cd pr-to-prompt
pnpm install
pnpm build
pnpm test
```

## Development Workflow

1. Fork and create a feature branch from `main`
2. Make your changes
3. Run the full check suite: `pnpm check`
4. Open a PR with a clear description of what and why

## Code Standards

- TypeScript strict mode
- Biome for formatting and linting
- Tests for new functionality
- Keep changes focused and minimal

## Running Tests

```bash
pnpm test          # Run all tests
pnpm test:watch    # Watch mode
pnpm lint          # Lint check
pnpm typecheck     # Type check
```

## Architecture

- `src/core/schema/` — Zod schema for the prompt-spec format
- `src/core/github/` — GitHub API client and PR data fetching
- `src/core/parsing/` — Deterministic spec generation from PR metadata
- `src/core/risk/` — Risk classification heuristics
- `src/core/rendering/` — YAML, Markdown, and PR comment renderers
- `src/cli/` — CLI entrypoint
- `src/action/` — GitHub Action entrypoint

## Commit Messages

Use conventional commits:
- `feat:` new feature
- `fix:` bug fix
- `test:` test changes
- `docs:` documentation
- `chore:` maintenance
