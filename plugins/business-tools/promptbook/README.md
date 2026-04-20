# Promptbook — Claude Code Plugin

Build better. See your progress. Post the proof.

Promptbook is an opt-in analytics plugin for Claude Code. After setup consent, it tracks prompts, tokens, and build time, sends session metrics to [promptbook.gg](https://promptbook.gg), and turns each session into shareable progress.

## Install

```
/plugin marketplace add promptbookgg/claude-code-plugin
/plugin install promptbook
```

Then run `/promptbook:setup` to connect your account.
Setup includes the data disclosure and records your consent in `~/.promptbook/config.json`. Tracking starts on your next Claude Code session.

## What it tracks

- Prompt count
- Token usage (input, output, cache)
- Build time
- Lines changed
- Primary language
- Tool usage counts
- File extension counts

No source code or prompt content is ever sent. See the Privacy section below for exactly what is sent.

## How it works

The plugin registers four Claude Code hooks:

| Event | What it does |
|---|---|
| **SessionStart** | Creates a session file, loads recent context |
| **UserPromptSubmit** | Counts prompts |
| **PostToolUse** | Counts lines changed, tracks file types |
| **SessionEnd** | Finalizes stats, submits to promptbook.gg |

After each session, you'll see a link to your progress. A short background process may continue briefly after Claude exits so Promptbook can submit the build and generate the title/summary. Customize the title, summary, and screenshot on the web — then share it.

## Privacy

**What is sent to promptbook.gg:** session ID, project name, model, timestamps, prompt count, token counts, build time, lines changed, language, file extension counts (e.g. `{ts: 5, css: 2}`), and tool usage counts (e.g. `{Edit: 12, Read: 8}`).

**What is never sent:** source code, prompt content, file contents, file paths, or your working directory.

The plugin also generates a short title and summary by calling Claude Haiku through your own Claude credentials — this goes to Anthropic (same as any Claude Code usage), never to Promptbook.

Promptbook remains inactive until setup writes your consent into the local config file.

## History Backfill

After setup, you can optionally scan your local Claude Code history and upload past sessions from the bundled `backfill-history.js` script shipped with this plugin. The plugin does not download executable code at runtime for backfill.

You can audit everything: the hooks are right here in this repo.

## Alternative install

If you prefer a one-command setup without the plugin system:

```bash
bash <(curl -sL promptbook.gg/setup.sh)
```

## Links

- [promptbook.gg](https://promptbook.gg)
- [Discover](https://promptbook.gg) — see what others are building
- [Setup](https://promptbook.gg/setup) — browser-based setup flow
