# Mattyp Changelog (Automation)

Generate weekly/monthly changelogs with a hybrid **Skill + MCP** workflow: collect changes (GitHub/Slack/Git), synthesize release notes, validate structure/quality, then create a branch/PR.

## Quick Start

1) Create `.changelog-config.json` in your repo (copy from the example):

```bash
cp ${CLAUDE_PLUGIN_ROOT}/config/changelog-config.example.json .changelog-config.json
```

2) Set required environment variables:

```bash
export GITHUB_TOKEN="ghp_..."
# Optional:
export SLACK_TOKEN="xoxb-..."
```

3) Run:
- `/changelog-validate` (sanity checks)
- `/changelog-weekly` (last 7 days)
- `/changelog-custom start_date=YYYY-MM-DD end_date=YYYY-MM-DD`

## Files

- Config schema: `${CLAUDE_PLUGIN_ROOT}/config/changelog-config.schema.json`
- Example config: `${CLAUDE_PLUGIN_ROOT}/config/changelog-config.example.json`
- Skill: `${CLAUDE_PLUGIN_ROOT}/skills/changelog-orchestrator/SKILL.md`
- MCP server: `${CLAUDE_PLUGIN_ROOT}/scripts/changelog_mcp.py`

