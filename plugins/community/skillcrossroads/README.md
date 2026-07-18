# skillcrossroads

Audit Claude Code artifacts from inside Claude Code.

Installing this plugin adds the **audit-skill**, which runs the free
[skillcrossroads](https://www.npmjs.com/package/skillcrossroads) CLI (MIT) to grade skills,
subagents, slash commands, `.mcp.json` configs, and plugins. Every finding in the scorecard
cites file and line, and the skill walks the ranked fix list until the grade stops improving —
then offers an embeddable badge.

- Invoke it explicitly (it applies fixes to your files, so it never auto-fires) — ask Claude to
  run the audit-skill on your skill, or use the plugin's skill picker.
- Keyless scans score all six rubric categories deterministically; setting
  `ANTHROPIC_API_KEY` upgrades Triggering to an LLM judge and adds three more checks.
- Hosted scans, badges, per-check fix docs, and ecosystem reports:
  [skillcrossroads.com](https://skillcrossroads.com) ·
  [check reference](https://skillcrossroads.com/docs/checks)

Upstream source: [github.com/sgharlow/skillcrossroads](https://github.com/sgharlow/skillcrossroads)
(the `skill/` directory is the canonical copy of this skill).
