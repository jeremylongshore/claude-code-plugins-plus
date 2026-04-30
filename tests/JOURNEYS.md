# Journeys — Tons of Skills / claude-code-plugins-plus-skills

> **Status:** policy-zone (engineer-owned). Each journey maps a persona-driven
> flow to the concrete repo artifacts that exercise (or fail to exercise) it.
> A step marked `(uncovered)` means there is no automated check today — fixing
> it means filing an issue and wiring a test, not deleting the row.
>
> **Cross-references.** Personas defined in [`PERSONAS.md`](./PERSONAS.md).
> Requirements catalogued in [`RTM.md`](./RTM.md). Existing test specs live
> under `marketplace/tests/T*.spec.ts` (dev) and
> `marketplace/tests/production/P*.spec.ts` (production).

---

## J1 — Plugin Author submits a new plugin

**Persona:** Pat (Plugin Author).

| # | Step | Coverage |
|---|------|----------|
| 1 | Fork `jeremylongshore/claude-code-plugins`, clone locally | `CONTRIBUTING.md` § "Adding a Plugin" |
| 2 | Copy from `templates/{minimal,command,agent,full}-plugin/` | Templates exist + are exercised by `validate-plugins.yml` `validate` job (catalog sync, structure check) |
| 3 | Edit `.claude-plugin/plugin.json` — only allowed fields | `validate-plugins.yml` "Check plugin structure" step rejects unknown fields |
| 4 | Add `README.md`, optional `LICENSE`, content directories | `validate-plugins.yml` "Check plugin structure" requires `README.md` |
| 5 | Add entry to `.claude-plugin/marketplace.extended.json` | `validate-plugins.yml` "Sync CLI marketplace catalog" step + `pnpm run sync-marketplace` script |
| 6 | Run `./scripts/quick-test.sh` locally | `quick-test.sh` ([scripts/quick-test.sh](../scripts/quick-test.sh)) — runs build + lint + validator |
| 7 | Open PR | GitHub pre-fills `.github/PULL_REQUEST_TEMPLATE.md` |
| 8 | CI runs full validate-plugins.yml matrix | All jobs in `.github/workflows/validate-plugins.yml` |
| 9 | Gemini PR review posts inline comments | `.gemini/commands/gemini-review.toml` (project-specific prompt) |
| 10 | Pat addresses `[Critical]` and `[High]` findings | `(uncovered)` — review-comment-resolution loop is human, not gated |
| 11 | Maintainer reviews and merges | Branch protection on `main` requires `validate` + `marketplace-validation` checks |
| 12 | `publish-changed-packages.yml` publishes to npm if version bumped | `.github/workflows/publish-changed-packages.yml` |
| 13 | README contributor block updates with attribution | `(uncovered)` — manual edit per CONTRIBUTING § "Recognition" |

---

## J2 — Marketplace Consumer searches and installs

**Persona:** Maya (Marketplace Consumer).

| # | Step | Coverage |
|---|------|----------|
| 1 | Land on homepage `/` | `marketplace/tests/T1-homepage-search-redirect.spec.ts` |
| 2 | Type query in hero search | `T1` "should navigate to /explore when search input is focused" |
| 3 | Auto-redirect to `/explore?q=<query>` | `T1` waitForURL assertion |
| 4 | Browse results in fuzzy-search index | `T2-search-results.spec.ts` + Fuse.js index built by `marketplace/scripts/generate-unified-search.mjs` |
| 5 | Click a plugin card | `T7-explore-plugin-flows.spec.ts` |
| 6 | Land on `/plugins/<slug>/` detail page | Generated from `src/pages/plugins/[name].astro`; routes validated by `marketplace/scripts/validate-routes.mjs` |
| 7 | Read description, see verification badge | `marketplace/scripts/extract-readme-sections.mjs` populates the page; production smoke covered by `tests/production/P1-core-pages.spec.ts` |
| 8 | Copy install command | `T4-install-cta.spec.ts` |
| 9 | Paste `/plugin install ... --project` into Claude Code | `(uncovered)` — happens outside the marketplace, in Claude Code itself |
| 10 | Install completes, plugin available immediately | `(uncovered)` — Claude Code internal behavior |

**Mobile variant:** every step above runs against `webkit-mobile`
(iPhone 13) + `chromium-mobile` (Pixel 5) projects in
`playwright.config.ts`. `T3-mobile-viewport.spec.ts` and
`production/P6-mobile-responsive.spec.ts` cover viewport-specific
behavior. `astro.config.mjs` keeps `compressHTML: false` to prevent
the iOS Safari >5000-char-line crash regression.

---

## J3 — Marketplace Consumer downloads cowork bundle (offline install)

**Persona:** Maya (Marketplace Consumer), offline-install variant.

| # | Step | Coverage |
|---|------|----------|
| 1 | Visit `/cowork/` page | `marketplace/tests/T8-cowork-page.spec.ts` |
| 2 | Browse available zip bundles | `T8` + `T9-cowork-integration.spec.ts` |
| 3 | Click download link for mega-zip / category bundle | `T8` + `production/P5-cowork-downloads.spec.ts` |
| 4 | Manifest matches downloaded file checksum | `marketplace/scripts/validate-cowork-downloads.mjs` (build-time) |
| 5 | Zip contains no secrets / `node_modules` | `marketplace/scripts/validate-cowork-security.mjs` (build-time) |
| 6 | Unzip locally, install offline | `(uncovered)` — happens on user's machine |

---

## J4 — MCP Integrator installs an MCP server plugin

**Persona:** Mei (MCP Integrator).

| # | Step | Coverage |
|---|------|----------|
| 1 | Browse `/explore?type=plugin` filtered to MCP plugins | `T7-explore-plugin-flows.spec.ts` (filter UI), `validate-routes.mjs` (URL params) |
| 2 | Click an MCP plugin → land on detail page | `src/pages/plugins/[name].astro` |
| 3 | `npm install -g @intentsolutionsio/<plugin>` | `(uncovered for end-user install)` — but the published artifact's shape is locked by `cli-smoke-tests` job semantics applied to MCP packages via `publish-changed-packages.yml` |
| 4 | Binary `dist/index.js` exists with shebang + executable bit | `validate-plugins.yml` `test` job (matrix) builds each MCP plugin and `chmod +x dist/index.js`; CI fails if missing |
| 5 | Wire MCP server into Claude Code config (`.mcp.json`) | `(uncovered)` — in user's Claude Code |
| 6 | `/mcp` lists registered tools | `(uncovered)` — Claude Code runtime |
| 7 | Vendor releases new SDK → maintainer bumps version | `publish-changed-packages.yml` ships only versions not yet on npm |

---

## J5 — CLI User runs ccpi commands

**Persona:** Casey (CLI User).

| # | Step | Coverage |
|---|------|----------|
| 1 | `npm install -g @intentsolutionsio/ccpi` | `cli-publish.yml` ships the package; `cli-smoke-tests` runs `npm pack` + `--dry-run` on every PR |
| 2 | `ccpi --help` exits 0 with full command list | `cli-smoke-tests` "Test CLI --help" step |
| 3 | `ccpi --version` prints version | `cli-smoke-tests` "Test CLI --version" step |
| 4 | `ccpi marketplace-add` writes catalog config | `cli-smoke-tests` "Test CLI marketplace-add" — `(partially covered: --help only)` |
| 5 | `ccpi list --all` returns full catalog | `(uncovered)` — depends on live catalog fetch |
| 6 | `ccpi install <plugin>` prints install command | `cli-smoke-tests` "Test CLI install command options" — `(partially covered: --help only)` |
| 7 | `ccpi doctor` runs system diagnostics | `cli-smoke-tests` "Test CLI doctor command" — `(partially covered: --help only)` |
| 8 | `ccpi validate --strict` exits non-zero on failure | `cli-smoke-tests` "Test CLI validate command" — `(partially covered: --help only)` |
| 9 | Install size stays under budget | `cli-smoke-tests` "Bundle size budget" step (`packages/cli/.size-limit.json`) — issue #591 |

---

## J6 — Pack Subscriber installs a SaaS pack

**Persona:** Sam (Pack Subscriber).

| # | Step | Coverage |
|---|------|----------|
| 1 | Browse `/explore?type=pack` | `T7-explore-plugin-flows.spec.ts` (filter UI) |
| 2 | Click a SaaS pack (e.g. `langchain-py-pack`) | `src/pages/plugins/[name].astro` resolves pack route |
| 3 | Read pack README — overview + skill list | `validate-internal-links.mjs` checks internal links in dist |
| 4 | `ccpi install --pack <name>` | `(uncovered for end-user install)` — pack install logic in `packages/cli/src/commands/install.ts` |
| 5 | Each skill in pack passes marketplace-tier validator | `scripts/validate-skills-schema.py --marketplace` (run in `validate-plugins.yml` `test` job) |
| 6 | `compatibility:` field accurate for vendor SDK version | `(uncovered for accuracy)` — schema validates the *field*, not vendor-version drift |
| 7 | External vendor links in skills resolve | `(uncovered)` — only internal links checked by `validate-internal-links.mjs` (REQ-016) |
| 8 | Vendor releases new SDK → maintainer bumps `compatibility:` | `(uncovered)` — no automated drift detection |

---

## J7 — Plugin Author addresses Gemini PR review

**Persona:** Pat (Plugin Author), feedback loop.

| # | Step | Coverage |
|---|------|----------|
| 1 | CI completes → Gemini bot posts inline review | `.gemini/commands/gemini-review.toml` defines the review prompt |
| 2 | Pat reads `[Critical]` / `[High]` / `[Medium]` / `[Low]` findings | Gemini severity classification (per CONTRIBUTING § "What happens when you open the PR") |
| 3 | Pat pushes a fix | Re-runs full `validate-plugins.yml` |
| 4 | Gemini re-reviews | `.gemini/commands/gemini-review.toml` re-runs |
| 5 | Maintainer follows up if Gemini was wrong | `(uncovered)` — human review escalation, no automation |
| 6 | All blocking findings cleared → merge | Branch protection requires `validate` + `marketplace-validation` checks |

---

## J8 — Accessibility-blind user navigates marketplace (a11y)

**Persona:** Maya (Marketplace Consumer), a11y variant. Issue #588.

| # | Step | Coverage |
|---|------|----------|
| 1 | Land on `/` with screen reader | `marketplace/tests/a11y/homepage.a11y.spec.ts` (axe-core, WCAG 2.0/2.1 A+AA) |
| 2 | Tab to hero search → focus visible | `(uncovered)` — focus-management is part of axe's `focus-order-semantics` rule but not all keyboard journeys |
| 3 | Search submit redirects to /explore | a11y spec covers `/explore/` chrome (results-grid excluded; tracked by REQ-021) |
| 4 | Filter UI on /explore is accessible | a11y spec scans `/explore/` excluding `#results-grid` (the catalog cards themselves are covered by detail pages) |
| 5 | Plugin detail page is accessible | a11y spec covers `/plugins/git-commit-smart/` as representative |
| 6 | Skill detail page is accessible | a11y spec covers `/skills/cursor-advanced-composer/` as representative |
| 7 | Docs hub navigable by keyboard | a11y spec covers `/docs/` |
| 8 | Color-contrast meets WCAG AA | Day-one baseline ceiling: 5 violations per page (currently passing at 1–3). `TODO(a11y-cleanup-followup)`: drive to 0. |

---

## J9 — Repo maintainer cuts a CLI release

**Persona:** Maintainer (not in PERSONAS.md — internal-only flow). Captured here
because it's a real journey that's only partially automated.

| # | Step | Coverage |
|---|------|----------|
| 1 | Bump `packages/cli/package.json` version | Manual |
| 2 | Push commit + tag `cli-v<x.y.z>` | Manual |
| 3 | `cli-publish.yml` triggers on tag | `.github/workflows/cli-publish.yml` |
| 4 | Build, test, publish to npm | `cli-publish.yml` |
| 5 | Bundle size verified | New: `cli-smoke-tests` "Bundle size budget" step (issue #591) |
| 6 | Released version available via `npm install -g @intentsolutionsio/ccpi` | `(uncovered post-publish)` — no smoke install of the live npm tarball |

---

## When to mark a step `(uncovered)`

- No CI job, no script, no smoke test exercises this step.
- Marking it `(uncovered)` is a **promise to file a follow-up issue** —
  not a permanent escape hatch.
- Cross-reference the followup issue here when it lands. Example:
  `(uncovered) → #621 Phase 5 PR1 wires git hooks`.

## When to add a new journey

Add a J-row when there's a real persona doing a real flow that today
fails silently. New J-rows must reference at least one step in PERSONAS.md
and link to a concrete file path or test name.
