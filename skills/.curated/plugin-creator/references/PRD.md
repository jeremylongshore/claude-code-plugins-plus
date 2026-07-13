# PRD: Plugin Creator

**Version:** 1.0.0
**Author:** Jeremy Longshore <jeremy@intentsolutions.io>
**Status:** Active
**Marketplace:** [tonsofskills.com](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io)
**Portfolio:** [jeremylongshore.com](https://jeremylongshore.com)

---

## Problem Statement

Creating a new Claude Code plugin requires generating multiple interdependent files (plugin.json, README.md, LICENSE, component files) in the correct directory structure, adding a catalog entry to marketplace.extended.json, running marketplace sync, and passing validation. Doing this manually is error-prone: developers forget required fields, use wrong directory structures, misconfigure frontmatter, or skip marketplace registration. Each mistake is caught only at CI time, adding iteration cycles.

## Target Users

| User | Context | Primary Need |
|------|---------|-------------|
| Plugin Author | Creating a new plugin from scratch | Complete scaffolding with all required files, correct structure, and marketplace registration |
| Community Contributor | Adding a plugin to the marketplace for the first time | Guided creation that follows all repository conventions without prior knowledge |
| Internal Developer | Rapidly prototyping new plugin ideas | Fast scaffolding that produces a CI-passing plugin on first commit |

## Success Criteria

1. Generated plugin passes `./scripts/validate-all-plugins.sh` without modifications
2. All required files created: `plugin.json`, `README.md`, `LICENSE`, and at least one component directory
3. Marketplace entry added to `marketplace.extended.json` and `marketplace.json` regenerated via sync
4. Plugin structure matches the category and type (commands/agents/skills/MCP) specified in the request

## Functional Requirements

1. Gather requirements: plugin name (kebab-case), category, type (commands/agents/skills/MCP/hybrid), description, and keywords
2. Create the directory structure under `plugins/[category]/[plugin-name]/`
3. Generate `.claude-plugin/plugin.json` with all required fields (name, version, description, author, license, keywords)
4. Generate `README.md` with installation, usage, and description sections
5. Create `LICENSE` file with MIT text (or specified license)
6. Generate component files with proper YAML frontmatter based on plugin type
7. Add the plugin entry to `.claude-plugin/marketplace.extended.json`
8. Run `pnpm run sync-marketplace` to regenerate `marketplace.json`
9. Validate with `./scripts/validate-all-plugins.sh plugins/[category]/[plugin-name]/`

## Non-Functional Requirements

- Plugin names must be kebab-case and unique across the entire catalog
- Generated `plugin.json` must contain only allowed fields (no extra fields that CI rejects)
- All generated `.sh` files must have execute permissions set
- MCP plugins must include `package.json`, `tsconfig.json`, and build configuration
- Generated README must follow the repository's standard format with installation and usage sections
- Default version for new plugins is `1.0.0`
- Keywords array must contain at least 2 entries for marketplace search discoverability

## Dependencies

- Write access to the `plugins/` directory and `.claude-plugin/marketplace.extended.json`
- `jq` installed for JSON generation and validation
- `pnpm run sync-marketplace` available at the repository root
- `./scripts/validate-all-plugins.sh` available for validation

## Out of Scope

- Implementing the actual skill/command/agent logic (scaffolding only)
- Publishing to external registries
- Generating test files for MCP plugins
- Migrating existing plugins between categories
- Generating reference documentation (PRD, ARD, errors.md, etc.)
- Version bumping after creation (handled by version-bumper)
