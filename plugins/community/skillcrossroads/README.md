# skillcrossroads

Audit Claude Code artifacts from inside Claude Code.

Installing this plugin adds the **audit-skill**, which runs the free
[skillcrossroads](https://www.npmjs.com/package/skillcrossroads) CLI (MIT) to grade skills,
subagents, slash commands, `.mcp.json` configs, and plugins. Every finding in the scorecard
cites file and line, and the skill walks the ranked fix list until the grade stops improving —
then offers an embeddable badge.

- Say: *"audit my skill"*, *"grade my skill"*, *"why doesn't my skill trigger"*, or
  *"lint my SKILL.md"*.
- Keyless scans score all six rubric categories deterministically; setting
  `ANTHROPIC_API_KEY` upgrades Triggering to an LLM judge and adds three more checks.
- Hosted scans, badges, per-check fix docs, and ecosystem reports:
  [skillcrossroads.com](https://skillcrossroads.com) ·
  [check reference](https://skillcrossroads.com/docs/checks)

Upstream source: [github.com/sgharlow/skillcrossroads](https://github.com/sgharlow/skillcrossroads)
(this `plugin/` directory is the canonical copy, mirrored into the marketplace by
`sources.yaml` - edit it here, never in the mirror).

## Package naming

Two npm packages are involved, with different owners by design:

- **`skillcrossroads`** (un-scoped) — the CLI this skill runs, published and maintained
  from the upstream source repo above. The skill pins it (`npx skillcrossroads@0.11.3`).
- **`@intentsolutionsio/skillcrossroads`** — the `package.json` in *this* directory. It is
  the marketplace's generated tracking/proof artifact (every catalog plugin is scaffolded
  under the `@intentsolutionsio` scope for npm download tracking) and is not the CLI.
  Install the plugin via `ccpi install skillcrossroads` or
  `/plugin install skillcrossroads@claude-code-plugins-plus` — not from that npm package.
