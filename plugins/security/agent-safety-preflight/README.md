# Agent Safety Preflight

Claude Code command plugin for generating a lightweight repository risk receipt before AI-agent edits.

Use it when a maintainer, teammate, or agent operator needs a quick green/yellow/red preflight before allowing Claude Code, Codex, Cursor, MCP-backed agents, or other coding agents to change a real repository.

## Installation

```bash
/plugin install agent-safety-preflight@claude-code-plugins-plus
```

## Usage

```bash
/agent-preflight
# or shortcut
/apf
```

## What it checks

- Git working-tree state and uncommitted-change risk.
- Files commonly used for agent authority, hooks, MCP routing, CI, and dangerous automation.
- High-risk command patterns such as destructive recursive deletion, shell-to-network install chains, credential writes, and agent authority config.
- A clear decision receipt: Green, Yellow, or Red, with the reason to stop or proceed.

## Privacy and safety

The bundled command is local-first. It does not require secrets, API keys, network access, KYC, payment credentials, or security testing against third-party systems. It is intended as a preflight receipt before routine AI-agent coding work, not as a vulnerability scanner.

## Open-source upstream

This marketplace package wraps the free command/scanner workflow from:

<https://github.com/el-zachariah/ai-agent-safety-starter-pack>

## Files

- `commands/agent-preflight.md` — Claude Code slash-command instructions.
- `scripts/agent_preflight_lite.py` — dependency-free local scanner used by the command.
- `tests/test_agent_preflight_lite.py` — basic parser/decision tests.

## License

MIT
