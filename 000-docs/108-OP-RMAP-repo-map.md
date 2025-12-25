# Repo Map (Operator Guide)

Repo: `jeremylongshore/claude-code-plugins-plus-skills` (local clone folder name may differ)

Mission framing:
- **Phase 0**: docs + repo hygiene only (no UI/CSS changes).
- **Phase 1+**: feature/work flows, refactors, UI work, dependency policy changes.

## Source-of-Truth Areas (core surfaces)

- `marketplace/` — Astro static site (npm-based project; deployed via GitHub Pages).
- `packages/cli/` — CLI workspace package (`@claude-code-plugins/ccp`).
- `plugins/mcp/*` — MCP server plugins (TypeScript/Node).
- `scripts/` — Validators + repo automation (sync, checks, audits).

## Top-Level Directory Map

- `.claude-plugin/` — Marketplace catalogs (`marketplace.extended.json` is source-of-truth; `marketplace.json` generated).
- `.beads/` — Beads issue DB + sync state (do not hand-edit).
- `000-docs/` — Operator/research documents (flat directory).
- `marketplace/` — Website (Astro + Tailwind) + Playwright tests.
- `packages/` — Workspace packages (CLI, analytics daemon, etc).
- `plugins/` — Instruction plugins + MCP plugins.
- `playbooks/` / `tutorials/` / `workspace/` — Learning lab + training materials.

## Buildable / Deployable Components

- **Buildable (pnpm workspace)**: `packages/*` + `plugins/mcp/*` via root `pnpm build`.
- **Deployable (website)**: `marketplace/` via `npm run build` (inside `marketplace/`).
- **Deploy triggers**: See `.github/workflows/` (do not change in Phase 0).

## Golden Paths (Local Development)

### Repo-wide validation (facts; do not change policy in Phase 0)

```bash
# Root workspace (pnpm)
pnpm -v
pnpm build
pnpm test
pnpm lint
pnpm typecheck
```

### Marketplace (website)

```bash
cd marketplace
npm run dev
npm run build
npm run preview
```

### Plugin validation

```bash
./scripts/validate-all-plugins.sh
./scripts/validate-all-plugins.sh plugins/mcp/<plugin>/
python3 scripts/validate-frontmatter.py
python3 scripts/validate-skills-schema.py
```

## Dependency Manager Inventory (facts only; Phase 0)

Observed lockfiles (example evidence commands in Phase 0 outputs):
- Root workspace lockfile: `pnpm-lock.yaml`
- Marketplace lockfile: `marketplace/package-lock.json`
- Generated/derived (not source-of-truth): `node_modules/.pnpm/lock.yaml`, `marketplace/node_modules/.package-lock.json`

Current policy (documented in `CLAUDE.md`):
- **Root + workspaces**: `pnpm` (enforced by CI checks)
- **Marketplace only**: `npm` (separate project under `marketplace/`)

Why there are two lockfiles (high-level):
- Workspace packages share pnpm tooling + workspace linking.
- Marketplace runs as its own npm project and keeps its own lockfile.

Phase 0 rule:
- Record confusion/drift as a punchlist item; do **not** migrate tooling in Phase 0.

