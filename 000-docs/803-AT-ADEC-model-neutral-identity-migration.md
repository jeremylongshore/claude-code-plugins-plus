<!-- doc-class: record -->

# Model-Neutral Identity and Distribution Migration

- **Date:** 2026-08-26
- **Authority:** 000-docs/727 §5 amendment; Epic 11 `claude-rblh`
- **Status:** Approved implementation decision

## Decision

Tons of Skills is a model-neutral Agent Skills marketplace. Its canonical GitHub
repository name is `jeremylongshore/tons-of-skills-marketplace`; its public product
and website remain **Tons of Skills** and `tonsofskills.com`.

The marketplace distributes one portable source skill, installed into each verified
harness's native discovery path. Native extensions are a separate product class.
They are never presented as portable skills merely because they share a marketplace.

## Compatibility contract

- Keep `plugins/` and `skills/` paths unchanged.
- Preserve legacy GitHub URL redirects and the legacy install slug as compatibility
  aliases. Existing npm package names and the `ccpi` command remain until a separate
  package-migration decision has evidence and a deprecation window.
- New public CLI capability is exposed under the `tons skills` command family; the
  existing `ccpi` behavior remains Claude Code plugin management.
- A harness may be named publicly only when the registry records it as
  `verified-native`. `standard-compatible` is an engineering status, not a marketing
  claim. Unknown or unsupported harnesses refuse installation with an explanation.

## Portable skills and native extensions

Portable skills use the open Agent Skills `SKILL.md` contract and retain one canonical
source tree. The installer may copy that source atomically into a harness's documented
native location, but the repository does not maintain harness-specific duplicate trees.

Omarchy Quattro/QML shell plugins are `native-extension` artifacts. Their installation
uses Omarchy's own explicit confirmation flow and manifest contract; they are catalogued
and tested separately from Agent Skills.

## Migration gate

The GitHub rename occurs only after the repository-identity preflight verifies old URL
redirect behavior, Actions/OIDC/deployment references, documentation URLs, git remote
guidance, and a rollback path. The rename does not authorize npm publication, token
rotation, external registry changes, or path renames.
