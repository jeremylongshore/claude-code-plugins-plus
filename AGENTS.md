# Repository Guidelines

## Project Structure & Module Organization
The workspace anchors each shipping plugin under `plugins/`, grouped by capability (for example `plugins/mcp/domain-memory-agent` or `plugins/skill-enhancers/web-to-github-issue`). Marketplace collateral lives in `marketplace/`, while shared messaging and scaffolds reside in `prompts/`, `templates/`, and `scripts/`. Reference guides sit in `000-docs/`. Treat `archive/` and `backups/` as read-only history; duplicate content into an active package before editing.

## Build, Test, and Development Commands
Install dependencies with `pnpm install`. Workspace scripts (`pnpm dev`, `pnpm build`, `pnpm test`) fan out to packages that expose those tasks—add matching scripts in new plugins or scope with `pnpm --filter <package> <task>`. Finish by running targeted builds and tests before a PR, and invoke `pnpm sync-marketplace` when refreshing catalog data.

## Coding Style & Naming Conventions
The codebase targets Node 18+ ESM with TypeScript by default; JavaScript utilities sit in `commands/` and `scripts/`. Prettier 3 and ESLint 9 enforce style—run `pnpm exec prettier --check .` and `pnpm --filter <package> lint --if-present`. Use camelCase functions, PascalCase classes, and kebab-case directories that mirror exported tools (`servers/knowledge-base.ts`).

## Testing Guidelines
Vitest underpins testing. Keep suites in `tests/` with `.test.ts` (or `.test.js` for pure JS) and store fixtures beside them. Cover request and response edges for each MCP tool, then run `pnpm --filter <package> test -- --coverage` before review and note any regressions.

## Commit & Pull Request Guidelines
Commits follow Conventional Commits (`feat(scope):`, `fix:`, `chore:`) as reflected in `git log`. PRs must link issues or marketplace tickets, summarize behaviour changes, list local verification (`pnpm build`, `pnpm test`), and attach visuals for agent-facing work. Update README, manifests, and change notes when behaviour shifts.

## Security & Configuration Tips
Never commit secrets; keep credentials in environment variables and document them in package READMEs. Run the checks described in `SECURITY.md` and follow `SETUP.md` when enabling new MCP servers. Validate plugin manifests with `jq` and ensure shell utilities stay executable (`chmod +x`).
