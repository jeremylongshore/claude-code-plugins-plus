# Releasing

How npm package releases work in this repo. Maps the trigger ↔ version-bump ↔ publish ↔ tag ↔ release flow end to end.

## TL;DR

```
PR with code change           merge to main
        │                           │
        ▼                           ▼
auto-bump-on-pr.yml          publish-changed-packages.yml
  · detects which plugins'     · for each changed plugin where local
    source files changed         version is not yet on npm:
  · bumps each plugin's          · npm publish --provenance
    package.json patch           · git tag @scope/name@version
    version (X.Y.Z → X.Y.Z+1)    · gh release create (auto-generated notes)
  · commits the bump back
    to the PR branch
```

End-to-end: a code change reaches `pnpm update` users without any human version-management ritual. Each release produces a tag and a GitHub Release with the npm install command, source path, and auto-generated commit / PR notes.

## What gets released this way

`@intentsolutionsio/*` scoped packages — currently ~430 of them, covering:

- `plugins/<category>/<plugin>/` — AI-instruction plugins (markdown-only)
- `plugins/mcp/<plugin>/` — MCP server plugins (TypeScript)
- `plugins/saas-packs/<pack>/` — SaaS skill packs
- `packages/<pkg>/` — root packages (CLI, analytics-daemon, etc.)

Anything outside `@intentsolutionsio/*` (legacy-named packages, third-party publishes) is not handled by this pipeline.

The CLI (`@intentsolutionsio/ccpi` in `packages/cli/`) has a separate tag-driven publish workflow (`cli-publish.yml`) for now and is not auto-bumped.

## When to override the auto-bump

The auto-bumper always picks **patch** because it can't read intent. Override it when you actually shipped a feature or a breaking change.

### Minor bump (new feature, backwards-compatible)

In the same PR that adds the feature, edit the affected plugin's `package.json` `version` directly:

```diff
- "version": "1.2.3",
+ "version": "1.3.0",
```

The auto-bumper detects that `package.json` changed *along with* source files and steps aside (it bumps a plugin only when the plugin's source changed *and* its package.json didn't change in the same PR). Your manual minor bump rides through and the publish workflow ships it as `@scope/name@1.3.0`.

### Major bump (breaking change)

Same pattern. Edit the version manually:

```diff
- "version": "1.3.5",
+ "version": "2.0.0",
```

Call out the breaking change in the PR description so the auto-generated GitHub Release notes carry it forward.

### Skip the auto-bump entirely on a PR

Two ways:

1. Push to a branch starting with `automation/` (e.g., `automation/npm-stats`, `automation/external-sync`). The workflow skips these to avoid self-bumping its own generated PRs.
2. Add `[skip auto-bump]` to the PR title or body.

## Anatomy of a release

When `publish-changed-packages.yml` ships `@intentsolutionsio/langchain-pack@1.1.0`, here's what lands:

| Artifact | Where |
|---|---|
| npm tarball | `https://www.npmjs.com/package/@intentsolutionsio/langchain-pack/v/1.1.0` |
| Annotated git tag | `@intentsolutionsio/langchain-pack@1.1.0` (visible in `git tag --list`) |
| GitHub Release | https://github.com/jeremylongshore/claude-code-plugins-plus-skills/releases/tag/@intentsolutionsio/langchain-pack@1.1.0 |
| Provenance attestation | https://www.npmjs.com/package/@intentsolutionsio/langchain-pack/v/1.1.0?activeTab=provenance |

The GitHub Release auto-includes:

- Install command: `pnpm add @intentsolutionsio/langchain-pack@1.1.0`
- Source path within the monorepo
- Auto-generated commit / PR summary since the previous tag for *this* package

## The freeze fix (one-time)

A bulk version sweep (`scripts/bulk-bump-versions.mjs`) is provided to break the historical 1.0.0 freeze across all packages. Run it once when ready:

```bash
node scripts/bulk-bump-versions.mjs            # dry-run; shows the plan
node scripts/bulk-bump-versions.mjs --apply    # writes new versions
```

For each package: if local version equals the latest on npm, bumps one minor (`1.0.0 → 1.1.0`). If local is already ahead, leaves it alone. If the package isn't on npm at all, leaves the version alone (the publish workflow picks it up as a fresh publish on next merge).

The output is one diff that bumps every applicable plugin's `package.json` from `1.0.0 → 1.1.0`. Commit + push + merge → `publish-changed-packages.yml` republishes ~400 packages and creates ~400 tags + releases. **Stagger this**: it produces a 30-minute wave of npm publishes and a corresponding burst of tags / releases. Don't merge during a freeze window or right before a customer-facing event.

## Why this design (and not Changesets)

Changesets is the gold standard for npm monorepos with hand-curated release engineering — it produces semantic-correct bumps, manually-authored CHANGELOG entries, and a "Version Packages" PR you can review before publishing. It works great when:

- Your monorepo has tens of packages, not hundreds
- Each package has hand-written API surface that benefits from semver discipline
- Engineers can be expected to author a `.changeset/*.md` per PR

This monorepo has 400+ packages, most of which are markdown-only AI instruction sets. Asking 16 contributors to author a changeset on every PR (or run a bot to fail PRs without one) is friction with no upside for that bulk. The auto-bump-on-change + manual override pattern gives:

- Zero PR-author burden for the common case (patch bump on incremental edits)
- Explicit override for intentional minor / major bumps
- Per-package tags + GitHub Releases with auto-generated notes (matching what Changesets would produce, just sourced from commit history rather than hand-written entries)

If the package mix shifts — fewer markdown plugins, more hand-curated APIs — switching to Changesets later is straightforward. The baseline that `bulk-bump-versions.mjs` establishes (1.1.0) is a clean starting point for either system.

## Failure modes + recovery

| Symptom | Cause | Fix |
|---|---|---|
| `auto-bump-on-pr` fails on `git push` to PR branch | Forked PR (no write access) | Author manually bumps `package.json` patch in their PR. The publish workflow then ships it on merge. |
| `publish-changed-packages` fails on one package | Stale `npm publish` token, missing `provenance` perms, name collision | Check the workflow log. Fix root cause, then bump the affected package's patch in a follow-up PR to retry. |
| Tag was created but publish failed | Order: publish first, then tag. If you see this, something raced. | Delete the orphan tag (`git push origin :refs/tags/<tag>`) and bump the patch to retry. |
| `gh release create` fails | Permissions or transient API hiccup | The publish + tag still landed; create the release manually with `gh release create <tag> --generate-notes`. |
| 429 rate-limit on `npm publish` (very rare) | Burst-publishing too many packages at once | The workflow sleeps 2s between publishes. If you hit this, split the merge into smaller batches. |

## Operational guardrails

- **Branch protection on `main`:** `validate` + `marketplace-validation` are the only required checks. Both must be green for merge. The `auto-bump-on-pr` workflow is informational — it always runs, but doesn't block merges.
- **No skipping hooks (`--no-verify`)** in normal commits. The workflows that do use `--no-verify` are explicitly bot-authored and bypass husky/prettier OOM in CI.
- **No force pushes to `main`.** Tag pushes (`refs/tags/*`) are allowed via `contents: write`.
- **npm provenance is on.** Every publish carries an attestation tying the tarball to this repo + commit, visible in npm's UI.
