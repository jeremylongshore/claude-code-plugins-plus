<!-- doc-class: research -->

# Harness Compatibility Matrix Research

- **Date:** 2026-08-26
- **Authority:** 803 decision; machine state is `config/harness-registry.json`
- **Status:** Initial primary-source baseline

The registry, not this document, owns live paths and support status. This record
captures the sources that justify the initial candidate set and requires a dated
fresh-environment test before public `verified-native` status.

On 2026-08-26, the initial source set was rechecked over HTTPS. The registry now
carries that date per entry; source availability is research evidence only and
does not upgrade a candidate to public support.

| Harness        | Initial classification        | Primary reference                                                                                               |
| -------------- | ----------------------------- | --------------------------------------------------------------------------------------------------------------- |
| Devin          | standard-compatible candidate | https://docs.devin.ai/product-guides/skills                                                                     |
| Kilo           | standard-compatible candidate | https://github.com/Kilo-Org/kilocode/blob/main/packages/kilo-docs/pages/customize/skills.md                     |
| OpenCode       | standard-compatible candidate | https://opencode.ai/docs/skills                                                                                 |
| Gemini CLI     | standard-compatible candidate | https://geminicli.com/docs/cli/skills/                                                                          |
| GitHub Copilot | standard-compatible candidate | https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills |
| Cursor         | standard-compatible candidate | https://prod.cursor.com/docs/skills                                                                             |
| Goose          | standard-compatible candidate | https://goose-docs.ai/docs/guides/context-engineering/using-skills/                                             |
| Amp            | standard-compatible candidate | https://ampcode.com/docs/customize/skills                                                                       |
| Roo            | standard-compatible candidate | https://roocodeinc.github.io/Roo-Code/features/skills/                                                          |
| Cline          | standard-compatible candidate | https://docs.cline.bot/customization/skills                                                                     |
| Kiro           | standard-compatible candidate | https://kiro.dev/docs/skills/                                                                                   |
| Omarchy        | native-extension only         | https://omarchy.org/manual/shell-plugins/                                                                       |

Claude Code, Codex, Pi, Hermes, and Windsurf remain registry candidates whose exact
runtime paths and test fixtures are owned by Epic 11 research and integration Beads.

## Promotion rule

Promotion to `verified-native` requires a pinned source URL, runtime version, project
and user scope path, successful fresh-environment discovery/activation proof, resource
behavior result, and installer rollback proof. A source-only assertion cannot promote
a harness.
